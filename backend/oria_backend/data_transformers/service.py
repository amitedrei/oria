from essentia.standard import MonoLoader, TensorflowPredictEffnetDiscogs, TensorflowPredict2D
from googletrans import Translator, LANGUAGES
from scipy.spatial.distance import cosine
from collections import Counter
from transformers import (
    AutoModel,
    pipeline,
)
from PIL import Image
from .models import (
    DistanceResponseModel,
    EmbeddingsResponseModel,
    TextToEmbeddingsModel,
    EmotionsResponseModel,
    TextToEmotionsModel,
    ImageToTextModel,
    TextResponseModel,
    UploadPostResponse,
    UploadPost,
    UploadSong
)
from io import BytesIO
import numpy as np
import torch
import re

# audio models constants
ESSENTIA_MODELS_PATH = '/content/drive/MyDrive/essentia_models/'
MOOD_EMBEDING_MODEL = 'discogs-effnet-bs64-1.pb'
MOOD_MODEL = 'mtg_jamendo_moodtheme-discogs_label_embeddings-effnet-1.pb'

MOOD_LABELS = [
    "action", "adventure", "advertising", "background", "ballad", "calm", "children", "christmas",
    "commercial", "cool", "corporate", "dark", "deep", "documentary", "drama", "dramatic", "dream",
    "emotional", "energetic", "epic", "fast", "film", "fun", "funny", "game", "groovy", "happy",
    "heavy", "holiday", "hopeful", "inspiring", "love", "meditative", "melancholic", "melodic",
    "motivational", "movie", "nature", "party", "positive", "powerful", "relaxing", "retro",
    "romantic", "sad", "sexy", "slow", "soft", "soundscape", "space", "sport", "summer", "trailer",
    "travel", "upbeat", "uplifting"
]
MOOD_THRESHOLD = 0.63

GENRE_LABELS = ['60s', '70s', '80s', '90s', 'acidjazz', 'alternative', 'alternativerock', 'ambient', 'atmospheric', 'blues', 'bluesrock', 'bossanova', 'breakbeat', 'celtic', 'chanson', 'chillout', 'choir', 'classical', 'classicrock', 'club', 'contemporary', 'country', 'dance', 'darkambient', 'darkwave', 'deephouse', 'disco', 'downtempo', 'drumnbass', 'dub', 'dubstep', 'easylistening', 'edm', 'electronic', 'electronica', 'electropop', 'ethno', 'eurodance', 'experimental', 'folk', 'funk', 'fusion', 'groove', 'grunge', 'hard', 'hardrock', 'hiphop', 'house', 'idm', 'improvisation', 'indie', 'industrial', 'instrumentalpop', 'instrumentalrock', 'jazz', 'jazzfusion', 'latin', 'lounge', 'medieval', 'metal', 'minimal', 'newage', 'newwave', 'orchestral', 'pop', 'popfolk', 'poprock', 'postrock', 'progressive', 'psychedelic', 'punkrock', 'rap', 'reggae', 'rnb', 'rock', 'rocknroll', 'singersongwriter', 'soul', 'soundtrack', 'swing', 'symphonic', 'synthpop', 'techno', 'trance', 'triphop', 'world', 'worldfusion']
GENRE_THRESHOLD = 0.63

ENGAGEMENT_LABELS = ['high', 'low']
ENGAGEMENT_THRESHOLD = 0.50

DANCEABLE_LABLES = ['True', "False"]
DANCEABLE_THRESHOLD = 0.50

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

image_to_text = pipeline("image-to-text", model="Salesforce/blip2-opt-2.7b")


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
    classifier_emotion = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        return_all_scores=True,
    )
    emotions = classifier_emotion(data.text)[0]

    classifier_label = pipeline(
        "zero-shot-classification", model="facebook/bart-large-mnli"
    )
    LABELS = [
        "Chill",
        "Energetic",
        "Intense",
        "Uplifting",
        "Dark",
        "Melancholic",
        "Playful",
        "Romantic",
        "Workout",
        "Relaxation",
        "Study",
        "Driving",
        "Party",
        "Focus",
        "Meditation",
        "Nature",
    ]
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
  filtered_labels = [(labels[i], round(average_predictions[i], 4)) for i in range(len(labels)) if average_predictions[i] > threshold]
  if not filtered_labels:
      max_prob = np.max(average_predictions)  # Find the highest probability
      filtered_labels = [(labels[i], round(average_predictions[i], 4)) for i in range(len(labels)) if average_predictions[i] == max_prob]
  final_labels = [label for label, score in filtered_labels]
  return final_labels

def get_audio_mood(embeddings):
  # use the model to extact mood/theme vector
  model = TensorflowPredict2D(graphFilename=f'{ESSENTIA_MODELS_PATH}mtg_jamendo_moodtheme-discogs_label_embeddings-effnet-1.pb')
  predictions = model(embeddings)

  return return_top_labels(predictions, MOOD_LABELS, MOOD_THRESHOLD)


def get_audio_genre(embeddings):
  # use the model to extact genre of the song
  model = TensorflowPredict2D(graphFilename=f"{ESSENTIA_MODELS_PATH}mtg_jamendo_genre-discogs-effnet-1.pb")
  predictions = model(embeddings)
  return return_top_labels(predictions, GENRE_LABELS, GENRE_THRESHOLD)

def get_engagment_level(embeddings):
  # use the model to classify if high or low engagment song
  model = TensorflowPredict2D(graphFilename=f"{ESSENTIA_MODELS_PATH}engagement_2c-discogs-effnet-1.pb", output="model/Softmax")
  predictions = model(embeddings)
  return return_top_labels(predictions, ENGAGEMENT_LABELS, ENGAGEMENT_THRESHOLD)

def is_dedanceable(embeddings):
  # use the model to decide if song is danceable
  model = TensorflowPredict2D(graphFilename=f"{ESSENTIA_MODELS_PATH}danceability-discogs-effnet-1.pb", output="model/Softmax")
  predictions = model(embeddings)
  return return_top_labels(predictions, DANCEABLE_LABLES, DANCEABLE_THRESHOLD)

async def get_audio_description(audio_path):
  audio = MonoLoader(filename=audio_path, sampleRate=16000, resampleQuality=4)()
  embedding_model = TensorflowPredictEffnetDiscogs(graphFilename=f"{ESSENTIA_MODELS_PATH}discogs-effnet-bs64-1.pb", output="PartitionedCall:1")
  embeddings = embedding_model(audio)

  genre = f"{', '.join(get_audio_genre(embeddings))}"
  mood = f"{', '.join(get_audio_mood(embeddings))}"
  engagment = f"{get_engagment_level(embeddings)[0]}"
  danceable = f"{is_dedanceable(embeddings)[0]}"
  return genre, mood, engagment, danceable


def translate_to_english(text):
    translator = Translator()
    detection = translator.detect(text)
    translation = translator.translate(text, dest='en')
    return translation.text


def identify_chorus(lyrics):
    # split to song sections
    lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
    sections = []
    current_section = []

    for line in lines:
        if not line:  
            if current_section:
                sections.append('\n'.join(current_section))
                current_section = []
        else:
            current_section.append(line)

    if current_section:
        sections.append('\n'.join(current_section))

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
                        chorus_candidates.append('\n'.join(candidate))

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
    title_words = set(re.findall(r'\b\w+\b', lines[0].lower()))

    for section in sections:
        section_lower = section.lower()
        title_word_count = sum(1 for word in title_words if word in section_lower)

        if title_word_count >= len(title_words) * 0.5:
            return section

    # if still unsuccessful, return the most common line
    line_counts = Counter(lines)
    return max(line_counts.items(), key=lambda x: x[1])[0]

async def get_lyrics_description(lyrics):
  en_lyrics = translate_to_english(lyrics)
  chorus = identify_chorus(en_lyrics)

  # extract emotions
  input_model = TextToEmotionsModel(text=chorus)
  emotions_result = await get_text_emotion(input_model)
  sorted_emotions = sorted(emotions_result.emotions, key=lambda x: x["score"], reverse=True)
  lyrics_emotions = [emotion['label'] for emotion in sorted_emotions if emotion['score'] > 0.65]
  if lyrics_emotions:
    return chorus, f"{', '.join(lyrics_emotions)}"
  return chorus, None

async def extract_song_description(audio_path, lyrics):
  genre, mood, engagment, danceable = await get_audio_description(audio_path)
  if not mood:
    mood = []
  if danceable:
    mood = f'{mood}, danceable'
  if engagment:
    mood = f'{mood}, engageable'

  chorus, lyrics_emotions = await get_lyrics_description(lyrics)
  if lyrics_emotions:
    mood = f'{mood}, {lyrics_emotions}'

  desc = ''
  if genre:
    desc += f'gener:{genre}\n'
  if mood:
    desc += f'feeling:{mood}\n'
  if chorus:
    desc += f'theme:{chorus}'
  return desc


async def extract_song_embedding(audio_path, lyrics):
  desc = await extract_song_description(audio_path, lyrics)
  input_model = TextToEmbeddingsModel(text=desc)
  embeddings_result = await get_embeddings(input_model)
  return embeddings_result.embeddings


async def get_description_for_post(data: UploadPost):
  model = ImageToTextModel(file=data.image)
  response = await get_image_text(model)
  image_as_text = response.text

  input_model = TextToEmotionsModel(text=data.text)
  emotions_result = await get_text_emotion(input_model)
  sorted_emotions = sorted(emotions_result.emotions, key=lambda x: x["score"], reverse=True)
  lyrics_emotions = [emotion['label'] for emotion in sorted_emotions if emotion['score'] > 0.65]

  desc = ''

  if lyrics_emotions:
    desc += f"feeling:{', '.join(lyrics_emotions)}\n"

  desc += f"theme:{image_as_text}\n"
  desc += f"saying:{data.text}"

  return desc

async def get_song_for_post(data: UploadPost):
  desc = get_description_for_post(data)
  input_model = TextToEmbeddingsModel(text=desc)
  embeddings_result = await get_embeddings(input_model)
  return embeddings_result
