import asyncio
from fastapi import APIRouter

from .models import (
    DistanceRequestModel,
    DistanceResponseModel,
    EmbeddingsResponseModel,
    TextToEmbeddingsModel,
    TextToEmotionsModel,
    EmotionsResponseModel
)
from .service import calculate_distance, get_embeddings, get_text_emotion


router = APIRouter(prefix="/data-transformers", tags=["Data Transformers"])

@router.post("/embeddings")
async def text_to_embeddings(data: TextToEmbeddingsModel) -> EmbeddingsResponseModel:
    return await get_embeddings(data)


@router.post("/calculate-distance")
async def get_distance(data: DistanceRequestModel) -> DistanceResponseModel:
    results = await asyncio.gather(
        get_embeddings(TextToEmbeddingsModel(text=data.text1)),
        get_embeddings(TextToEmbeddingsModel(text=data.text2)),
    )
    return calculate_distance(
        embedding1=results[0].embeddings, embedding2=results[1].embeddings
    )


@router.post("/text")
async def text_to_emotions(data: TextToEmotionsModel) -> EmotionsResponseModel:
    return await get_text_emotion(data)
