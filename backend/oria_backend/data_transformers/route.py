from fastapi import APIRouter

from .models import (
    DistanceRequestModel,
    DistanceResponseModel,
    EmbeddingsResponseModel,
    TextToEmbeddingsModel,
)
from .service import calculate_distance, get_embeddings

router = APIRouter(prefix="/data-transformers", tags=["Data Transformers"])


@router.post("/embeddings")
async def text_to_embeddings(data: TextToEmbeddingsModel) -> EmbeddingsResponseModel:
    return await get_embeddings(data)


@router.post("/calculate-distance")
async def get_distance(data: DistanceRequestModel) -> DistanceResponseModel:
    embeddings1 = (await get_embeddings(TextToEmbeddingsModel(text=data.text1))).embeddings
    embeddings2 = (await get_embeddings(TextToEmbeddingsModel(text=data.text2))).embeddings
    return calculate_distance(embedding1=embeddings1, embedding2=embeddings2)
