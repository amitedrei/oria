from typing import List

from pydantic import BaseModel


class SongResponseModel(BaseModel):
    id: str
    name: str
    artists: List[str]
    url: str
    source: str
    playlists: List[str]
    distances: dict[str, float] = {}
    distance: float = -1
    thumbnail: str
    percentage: float
