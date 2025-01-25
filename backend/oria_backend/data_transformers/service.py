import numpy as np
from scipy.spatial.distance import cosine, euclidean
from transformers import AutoModel, pipeline

from .models import (
    DistanceResponseModel,
    EmbeddingsResponseModel,
    TextToEmbeddingsModel,
    EmotionsResponseModel, 
    TextToEmotionsModel
)

embeddings_model = AutoModel.from_pretrained(
    "jinaai/jina-embeddings-v3", trust_remote_code=True
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
    classifier_emotion = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", return_all_scores=True)
    emotions = classifier_emotion(data.text)[0]

    classifier_label = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    LABELS = ["Chill", "Energetic", "Intense", "Uplifting", "Dark", "Melancholic",  "Playful", "Romantic", "Workout", "Relaxation", "Study", "Driving", "Party", "Focus", "Meditation", "Nature"]
    labels_scores = classifier_label(data.text, LABELS, multi_label=True)

    emotions.extend([{'label': label, 'score': score} for label, score in zip(labels_scores['labels'], labels_scores['scores'])])
    return EmotionsResponseModel(text=data.text, emotions=emotions)
