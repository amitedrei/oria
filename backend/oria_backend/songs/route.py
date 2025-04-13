from typing import Annotated

from fastapi import APIRouter, Form, UploadFile
from oria_backend.data_transformers.models import UploadPost
from oria_backend.songs.service import find_top_songs, get_all_songs

router = APIRouter(prefix="/songs", tags=["Songs"])


@router.get("/")
async def get_songs():
    return await get_all_songs()


@router.post("/find-songs")
async def find_songs(file: UploadFile, text: Annotated[str, Form()]):
    find_song_data = UploadPost(text=text, image=file)
    return await find_top_songs(find_song_data)
