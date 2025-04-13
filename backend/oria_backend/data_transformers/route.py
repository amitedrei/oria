import asyncio
from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse
import hashlib

from .models import (
    DistanceRequestModel,
    DistanceResponseModel,
    EmbeddingsResponseModel,
    ImageToTextModel,
    TextResponseModel,
    TextToEmbeddingsModel,
    TextToEmotionsModel,
    EmotionsResponseModel,
    UploadPostResponse,
    UploadPost,
    UploadSong
)
from .service import (
    calculate_distance,
    get_embeddings,
    get_image_text,
    get_text_emotion,
    extract_song_embedding,
    get_song_for_post
)

from pathlib import Path
import shutil
import os

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
    if not file.content_type.startswith("image/"):
        return JSONResponse(
            status_code=400,
            content={"message": "File must be an image"},
        )
    return await get_image_text(ImageToTextModel(file=file))

@router.post("/song")
async def upload_song(
    audio: UploadFile = File(...),
    lyrics: str = Form(...)
):
    print(audio.filename)
    file_path = f"{hashlib.sha256(audio.filename.encode()).hexdigest()}.wav"
    file_path = f"{str(UPLOAD_DIR)}/{file_path}"

    with open (file_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
    
    embedding = await extract_song_embedding(file_path, lyrics)
    os.remove(file_path)
    return embedding


@router.post("/post")
async def get_song_for_post_data(data: UploadPost):
    return await get_song_for_post(data)
