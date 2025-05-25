import re
from collections import Counter
from io import BytesIO

import numpy as np
import torch
from essentia.standard import (
    MonoLoader,
    TensorflowPredict2D,
    TensorflowPredictEffnetDiscogs,
)
from googletrans import Translator
from PIL import Image
from scipy.spatial.distance import cosine
from transformers import (
    AutoModel,
    pipeline,
)

from oria_backend.data_transformers.prompts.image_to_embeddings import (
    generate_image_to_embeddings_prompt,
)
from oria_backend.data_transformers.prompts.song_to_embeddings import (
    generate_song_to_embeddings_prompt,
)

from .consts import (
    DANCEABLE_LABLES,
    DANCEABLE_THRESHOLD,
    ENGAGEMENT_LABELS,
    ENGAGEMENT_THRESHOLD,
    ESSENTIA_MODELS_PATH,
    GENRE_LABELS,
    GENRE_THRESHOLD,
    LABELS,
    MOOD_LABELS,
    MOOD_THRESHOLD,
)
from .models import (
    DistanceResponseModel,
    EmbeddingsResponseModel,
    EmotionsResponseModel,
    ImageToTextModel,
    TextResponseModel,
    TextToEmbeddingsModel,
    TextToEmotionsModel,
    UploadPost,
)

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)

embeddings_model = AutoModel.from_pretrained(
    "jinaai/jina-embeddings-v3", trust_remote_code=True
).to(device)

classifier_emotion = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=None,
    device=device,
)

classifier_label = pipeline(
    "zero-shot-classification", model="facebook/bart-large-mnli", device=device
)
image_to_text = pipeline(
    "image-to-text", model="nlpconnect/vit-gpt2-image-captioning", device=device
)

song_embedding_model = TensorflowPredictEffnetDiscogs(
    graphFilename=f"{ESSENTIA_MODELS_PATH}/discogs-effnet-bs64-1.pb",
    output="PartitionedCall:1",
)

danceable_model = TensorflowPredict2D(
    graphFilename=f"{ESSENTIA_MODELS_PATH}/danceability-discogs-effnet-1.pb",
    output="model/Softmax",
)


engagement_model = TensorflowPredict2D(
    graphFilename=f"{ESSENTIA_MODELS_PATH}/engagement_2c-discogs-effnet-1.pb",
    output="model/Softmax",
)

genre_model = TensorflowPredict2D(
    graphFilename=f"{ESSENTIA_MODELS_PATH}/mtg_jamendo_genre-discogs-effnet-1.pb"
)


mood_model = TensorflowPredict2D(
    graphFilename=f"{ESSENTIA_MODELS_PATH}/mtg_jamendo_moodtheme-discogs_label_embeddings-effnet-1.pb"
)


async def get_embeddings(data: TextToEmbeddingsModel) -> EmbeddingsResponseModel:
    embeddings = embeddings_model.encode([data.text])
    return EmbeddingsResponseModel(text=data.text, embeddings=embeddings.tolist()[0])


def calculate_distance(
    embedding1: list[float], embedding2: list[float]
) -> DistanceResponseModel:
    embedding1 = np.array(embedding1)
    embedding2 = np.array(embedding2)

    cosine_sim = 1 - cosine(embedding1, embedding2)

    return DistanceResponseModel(similarity=cosine_sim)


async def get_text_emotion(data: TextToEmotionsModel) -> EmotionsResponseModel:
    emotions = classifier_emotion(data.text)[0]
    labels_scores = classifier_label(data.text, LABELS, multi_label=True)

    emotions.extend(
        [
            {"label": label, "score": score}
            for label, score in zip(labels_scores["labels"], labels_scores["scores"])
        ]
    )
    return EmotionsResponseModel(text=data.text, emotions=emotions)


async def get_image_text(data: ImageToTextModel) -> TextResponseModel:
    image = data.file.file.read()
    image = Image.open(BytesIO(image)).convert("RGB")
    image = image.resize((128, 128))
    preds = image_to_text(image)
    return TextResponseModel(text=preds[0]["generated_text"])


def return_top_labels(predictions, labels, threshold):
    # sum the vector for the deferent part of the song and select the top lables.
    summed_predictions = np.sum(predictions, axis=0)
    num_chunks = predictions.shape[0]
    average_predictions = summed_predictions / num_chunks
    filtered_labels = [
        (labels[i], round(average_predictions[i], 4))
        for i in range(len(labels))
        if average_predictions[i] > threshold
    ]
    if not filtered_labels:
        max_prob = np.max(average_predictions)  # Find the highest probability
        filtered_labels = [
            (labels[i], round(average_predictions[i], 4))
            for i in range(len(labels))
            if average_predictions[i] == max_prob
        ]
    final_labels = [label for label, score in filtered_labels]
    return final_labels


def get_audio_mood(embeddings):
    predictions = mood_model(embeddings)

    return return_top_labels(predictions, MOOD_LABELS, MOOD_THRESHOLD)


def get_audio_genre(embeddings):
    predictions = genre_model(embeddings)
    return return_top_labels(predictions, GENRE_LABELS, GENRE_THRESHOLD)


def get_engagment_level(embeddings):
    predictions = engagement_model(embeddings)
    return return_top_labels(predictions, ENGAGEMENT_LABELS, ENGAGEMENT_THRESHOLD)


def is_dedanceable(embeddings):
    predictions = danceable_model(embeddings)
    return return_top_labels(predictions, DANCEABLE_LABLES, DANCEABLE_THRESHOLD)


async def get_audio_description(audio_path):
    audio = MonoLoader(filename=str(audio_path), sampleRate=16000, resampleQuality=4)()

    embeddings = song_embedding_model(audio)

    genre = f"{', '.join(get_audio_genre(embeddings))}"
    mood = f"{', '.join(get_audio_mood(embeddings))}"
    engagment = f"{get_engagment_level(embeddings)[0]}"
    danceable = f"{is_dedanceable(embeddings)[0]}"
    return genre, mood, engagment, danceable


async def translate_to_english(text):
    translator = Translator()
    translation = await translator.translate(text, dest="en")
    return translation.text


async def identify_chorus_from_src(src_lyrics):
    chorus = ""
    for i in re.findall(r"(\[.*?\])+", src_lyrics):
        if chorus:
            index = chorus.find(i)
            if not index:
                continue
            chorus = chorus[:index]
            break
        else:
            res = await translate_to_english(i)
            if "chorus" in res.lower():
                index = src_lyrics.find(i)
                if not index:
                    continue

                chorus = src_lyrics[index + len(i) :]

    if chorus:
        return await translate_to_english(chorus)
    return chorus


async def identify_chorus(lyrics):
    # split to song sections
    lines = [line.strip() for line in lyrics.split("\n") if line.strip()]
    sections = []
    current_section = []

    for line in lines:
        if not line:
            if current_section:
                sections.append("\n".join(current_section))
                current_section = []
        else:
            current_section.append(line)

    if current_section:
        sections.append("\n".join(current_section))

    # if couldn't split to to sections
    if len(sections) <= 1:
        # look for cluster of repeated lines
        line_counts = Counter(lines)
        repeated_lines = [line for line, count in line_counts.items() if count >= 2]

        if repeated_lines:
            chorus_candidates = []
            for i in range(len(lines)):
                if lines[i] in repeated_lines:
                    candidate = [lines[i]]
                    for j in range(1, min(4, len(lines) - i)):
                        if lines[i + j] in repeated_lines:
                            candidate.append(lines[i + j])
                        else:
                            break

                    # add the cluster to candidates if at least 2 lines
                    if len(candidate) >= 2:
                        chorus_candidates.append("\n".join(candidate))

            # choose the longest candidate else most repeated line
            if chorus_candidates:
                return max(chorus_candidates, key=len)
            else:
                return max(line_counts.items(), key=lambda x: x[1])[0]
    else:
        # return the section that appear the most
        section_counts = Counter(sections)
        most_common_section = section_counts.most_common(1)[0][0]
        # verify it appeared at least 2 times
        if section_counts[most_common_section] >= 2:
            return most_common_section

    # fall return section containing the title
    title_words = set(re.findall(r"\b\w+\b", lines[0].lower()))

    for section in sections:
        section_lower = section.lower()
        title_word_count = sum(1 for word in title_words if word in section_lower)

        if title_word_count >= len(title_words) * 0.5:
            return section

    # if still unsuccessful, return the most common line
    line_counts = Counter(lines)
    return max(line_counts.items(), key=lambda x: x[1])[0]


async def get_lyrics_description(lyrics):
    chorus = await identify_chorus_from_src(lyrics)
    if not chorus:
        en_lyrics = await translate_to_english(lyrics)
        chorus = await identify_chorus(en_lyrics)

    # extract emotions
    input_model = TextToEmotionsModel(text=chorus)
    emotions_result = await get_text_emotion(input_model)
    sorted_emotions = sorted(
        emotions_result.emotions, key=lambda x: x["score"], reverse=True
    )
    lyrics_emotions = [
        emotion["label"] for emotion in sorted_emotions if emotion["score"] > 0.65
    ]
    if lyrics_emotions:
        return chorus, f"{', '.join(lyrics_emotions)}"
    return chorus, None


async def extract_song_description(audio_path, lyrics):
    genre, mood, engagment, danceable = await get_audio_description(audio_path)
    if not mood:
        mood = []
    if danceable:
        mood = f"{mood}, danceable"
    if engagment:
        mood = f"{mood}, engageable"

    chorus, lyrics_emotions = await get_lyrics_description(lyrics)
    if lyrics_emotions:
        mood = f"{mood}, {lyrics_emotions}"

    return genre, mood, chorus


async def extract_song_embeddings(audio_path, lyrics):
    genre, mood, chorus = await extract_song_description(audio_path, lyrics)

    input_model = TextToEmbeddingsModel(text=mood)
    mood_embedding = await get_embeddings(input_model)

    input_model = TextToEmbeddingsModel(text=chorus)
    chorus_embedding = await get_embeddings(input_model)

    return genre, mood_embedding.embeddings, chorus_embedding.embeddings
    

async def get_embeddings_for_post(data: UploadPost):
    model = ImageToTextModel(file=data.image)
    response = await get_image_text(model)
    image_as_text = response.text

    input_model = TextToEmotionsModel(text=data.text)
    emotions_result = await get_text_emotion(input_model)
    sorted_emotions = sorted(
        emotions_result.emotions, key=lambda x: x["score"], reverse=True
    )

    emotions = [
        emotion["label"] for emotion in sorted_emotions if emotion["score"] > 0.65
    ]

    input_model = TextToEmbeddingsModel(text=f'{image_as_text}\n{data.text}')
    description_embedding = await get_embeddings(input_model)

    input_model = TextToEmbeddingsModel(text=','.join(emotions))
    emotions_embedding = await get_embeddings(input_model)

    return description_embedding.embeddings, emotions_embedding.embeddings
