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

from functools import reduce
from googletrans import Translator
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
    UploadPost
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


async def get_lyrics_description(chorus):
    input_model = TextToEmotionsModel(text=chorus)
    emotions_result = await get_text_emotion(input_model)
    sorted_emotions = sorted(
        emotions_result.emotions, key=lambda x: x["score"], reverse=True
    )
    lyrics_emotions = [
        emotion["label"] for emotion in sorted_emotions if emotion["score"] > 0.65
    ]
    if lyrics_emotions:
        return f"{', '.join(lyrics_emotions)}"
    return None


async def extract_song_description(audio_path, chorus):
    genre, mood, engagment, danceable = await get_audio_description(audio_path)
    if not mood:
        mood = []
    if danceable:
        mood = f"{mood}, danceable"
    if engagment:
        mood = f"{mood}, engageable"

    lyrics_emotions = await get_lyrics_description(chorus)
    if lyrics_emotions:
        mood = f"{mood}, {lyrics_emotions}"

    return genre, mood


async def extract_song_embeddings(audio_path, lyrics, name, chorus):
    genre, mood = await extract_song_description(audio_path, chorus)

    input_model = TextToEmbeddingsModel(text=mood)
    mood_embedding = await get_embeddings(input_model)

    input_model = TextToEmbeddingsModel(text=lyrics)
    lyrics_embedding = await get_embeddings(input_model)

    input_model = TextToEmbeddingsModel(text=name)
    name_embedding = await get_embeddings(input_model)

    if chorus != lyrics:
        input_model = TextToEmbeddingsModel(text=chorus)
        chorus_embedding = await get_embeddings(input_model)
    else:
        chorus_embedding = lyrics_embedding

    return genre, mood_embedding.embeddings, lyrics_embedding.embeddings, chorus_embedding.embeddings, name_embedding.embeddings
    

async def get_embeddings_for_post(data: UploadPost):
    """
        get post data
    
        return:
        post_emmbedings -> emmbeding of the post text and photo combined
        emotions_embedding -> emmbeding of the post emotions
    """
    model = ImageToTextModel(file=data.image)
    response = await get_image_text(model)
    image_as_text = response.text
    
    data_text = None
    emotions_result = None
    
    if data.text:
        try:
            data_text = await translate_to_english(data.text)
        except Exception as e:
            data_text = data.text
            print(f"Translation failed: {e}")
    
    input_model = TextToEmbeddingsModel(text=f'{image_as_text}')
    image_embedding = await get_embeddings(input_model)
    emotions_result = None

    if data_text is not None:
        input_model = TextToEmbeddingsModel(text=data_text)
        description_embedding = await get_embeddings(input_model)
        post_emmbedings = [(a * 2 + b) / 3 for a, b in zip(description_embedding.embeddings, image_embedding.embeddings)]
        input_model = TextToEmotionsModel(text=data_text)
        emotions_result = await get_text_emotion(input_model)
    else:
        post_emmbedings = image_embedding.embeddings
    
    if not emotions_result:
        input_model = TextToEmotionsModel(text=image_as_text)
        emotions_result = await get_text_emotion(input_model)


    sorted_emotions = sorted(
        emotions_result.emotions, key=lambda x: x["score"], reverse=True
    )

    final_emotions = [
        emotion["label"] for emotion in sorted_emotions if emotion["score"] > 0.65
    ]
    if len(final_emotions) < 3:
        final_emotions = [
            emotion["label"] for emotion in sorted_emotions[0:3]
        ]

    emotions = reduce(lambda x, y: x + ', ' + y, final_emotions)

    input_model = TextToEmbeddingsModel(text=emotions)
    emotions_embedding = await get_embeddings(input_model)
    return post_emmbedings, emotions_embedding.embeddings, 