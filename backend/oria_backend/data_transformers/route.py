import asyncio
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from .models import (
    DistanceRequestModel,
    DistanceResponseModel,
    EmbeddingsResponseModel,
    ImageToTextModel,
    TextResponseModel,
    TextToEmbeddingsModel,
    TextToEmotionsModel,
    EmotionsResponseModel,
)
from .service import (
    calculate_distance,
    get_embeddings,
    get_image_text,
    get_text_emotion,
)


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


@router.post("/image")
async def upload_image(file: UploadFile = File(...)) -> TextResponseModel:
    if not file.content_type.startswith("image/"):
        return JSONResponse(
            status_code=400,
            content={"message": "File must be an image"},
        )
    return await get_image_text(ImageToTextModel(file=file))
