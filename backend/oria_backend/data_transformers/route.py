from fastapi import APIRouter, File, UploadFile

from .models import (
    EmbeddingsResponseModel,
    ImageToTextResponseModel,
    TextToEmbeddingsModel,
)
from .service import (
    extract_description_from_image,
    get_embeddings,
    get_image_from_upload_file,
)

router = APIRouter(prefix="/data-transformers", tags=["Data Transformers"])


@router.post("/text-to-embeddings")
async def text_to_embeddings(data: TextToEmbeddingsModel) -> EmbeddingsResponseModel:
    embeddings = get_embeddings(data.text)

    return EmbeddingsResponseModel(text=data.text, embeddings=embeddings)


@router.post("/image-to-text")
async def image_to_text(image: UploadFile = File(...)) -> ImageToTextResponseModel:
    image_description = extract_description_from_image(
        get_image_from_upload_file(image)
    )
    return ImageToTextResponseModel(image_description=image_description)

@router.post("/song")
async def get_songs_details(name: TextToEmbeddingsModel, chorus: TextToEmbeddingsModel):
    name_embedding = get_embeddings(name.text)
    chorus_embedding = get_embeddings(chorus.text)

    return [
        EmbeddingsResponseModel(text=name.text, embeddings=name_embedding),
        EmbeddingsResponseModel(text=chorus.text, embeddings=chorus_embedding)
    ]