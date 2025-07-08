from oria_backend.songs.models import LikeSongRequestModel, TopSongResponseModel
from oria_backend.songs.service import (
    get_all_songs,
    find_top_songs,
    like_song,
    unlike_song,
)
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, Query

router = APIRouter(prefix="/songs", tags=["Songs"])


@router.get("/")
async def get_songs(count: Optional[int] = Query(default=None, ge=1)):
    return await get_all_songs(count=count)


@router.post("/find-songs")
async def find_songs(
    text: str = Form(...), image: UploadFile = File(...)
) -> TopSongResponseModel:
    return await find_top_songs(image, text)


@router.post("/like")
async def like_song_request(data: LikeSongRequestModel):
    await like_song(data)


@router.post("/unlike")
async def unlike_song_request(data: LikeSongRequestModel):
    await unlike_song(data)
