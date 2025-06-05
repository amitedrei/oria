from pydantic import BaseModel


class TextToEmbeddingsModel(BaseModel):
    text: str


class EmbeddingsResponseModel(BaseModel):
    text: str
    embeddings: list[float]


class ImageToTextResponseModel(BaseModel):
    image_description: str
