from io import BytesIO
import numpy as np
from scipy.spatial.distance import cosine
import torch
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
