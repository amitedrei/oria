from typing import List

from pydantic import BaseModel

class SongResponseModel(BaseModel):
    id: str
    song_id: str
    name: str
    artists: List[str]
    url: str
    thumbnail: str
    source: str
    playlists: List[str]
    distance: float
