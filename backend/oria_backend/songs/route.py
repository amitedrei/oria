from fastapi import APIRouter, File, Form, UploadFile
from oria_backend.songs.service import find_top_songs, get_all_songs

router = APIRouter(prefix="/songs", tags=["Songs"])


@router.get("/")
async def get_songs():
    return await get_all_songs()


@router.post("/find-songs")
async def find_songs(text: str = Form(...), image: UploadFile = File(...)):
    return await find_top_songs(image, text)
