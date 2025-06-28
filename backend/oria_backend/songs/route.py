from oria_backend.songs.service import get_all_songs, find_top_songs
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, Query

router = APIRouter(prefix="/songs", tags=["Songs"])


@router.get("/")
async def get_songs(count: Optional[int] = Query(default=None, ge=1)):
    return await get_all_songs(count=count)


@router.post("/find-songs")
async def find_songs(text: str = Form(...), image: UploadFile = File(...)):
    return await find_top_songs(image, text)
