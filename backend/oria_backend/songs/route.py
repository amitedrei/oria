from fastapi import APIRouter, File, Form, UploadFile
from oria_backend.data_transformers.models import UploadPost
from oria_backend.songs.service import get_song_for_post

router = APIRouter(prefix="/songs", tags=["Songs"])


@router.post("/find-songs")
async def find_songs(text: str = Form(...), image: UploadFile = File(...)):
    find_song_data = UploadPost(text="" or text, image=image)
    return await get_song_for_post(find_song_data)
