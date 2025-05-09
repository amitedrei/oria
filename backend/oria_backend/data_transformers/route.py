import asyncio
import hashlib
import os
from pathlib import Path
import shutil
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from fastapi import HTTPException

from .models import (
    DistanceRequestModel,
    DistanceResponseModel,
    EmbeddingsResponseModel,
    EmotionsResponseModel,
    ImageToTextModel,
    TextResponseModel,
    TextToEmbeddingsModel,
    TextToEmotionsModel,
    UploadPost,
)
from .service import (
    calculate_distance,
    extract_song_embedding,
    get_embeddings,
    get_image_text,
    get_song_for_post,
    get_text_emotion,
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image",
        )
    return await get_image_text(ImageToTextModel(file=file))


@router.post("/song")
async def song_to_embeddings(audio: UploadFile = File(...), lyrics: str = Form(...)):
    file_path = f"{hashlib.sha256(audio.filename.encode()).hexdigest()}.wav"
    file_path = f"{str(UPLOAD_DIR)}/{file_path}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    embedding = await extract_song_embedding(file_path, lyrics)
    os.remove(file_path)
    return embedding


@router.post("/post")
async def get_song_for_post_data(
    text: Annotated[str, Form()], image: UploadFile = File(...)
):
    return await get_song_for_post(UploadPost(text=text, image=image))
