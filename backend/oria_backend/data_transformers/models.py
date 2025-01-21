from pydantic import BaseModel


class TextToEmbeddingsModel(BaseModel):
    text: str


class EmbeddingsResponseModel(BaseModel):
    text: str
    embeddings: list[float]


class DistanceRequestModel(BaseModel):
    text1: str
    text2: str


class DistanceResponseModel(BaseModel):
    similarity: float
