from pydantic import BaseModel
from fastapi import UploadFile


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


class TextToEmotionsModel(BaseModel):
    text: str


class EmotionsResponseModel(BaseModel):
    text: str
    emotions: list[dict]


class ImageToTextModel(BaseModel):
    file: UploadFile


class TextResponseModel(BaseModel):
    text: str
