from fastapi import APIRouter

from .service import get_embeddings

from .models import EmbeddingsResponseModel, TextToEmbeddingsModel

router = APIRouter(prefix="/data-transformers", tags=["Data Transformers"])


@router.post("embeddings")
async def text_to_embeddings(data: TextToEmbeddingsModel) -> EmbeddingsResponseModel:
    return await get_embeddings(data)
