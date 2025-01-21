import numpy as np
from scipy.spatial.distance import cosine, euclidean
from transformers import AutoModel

from .models import (
    DistanceResponseModel,
    EmbeddingsResponseModel,
    TextToEmbeddingsModel,
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
