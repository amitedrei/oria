from typing import List

from pydantic import BaseModel
from bson import ObjectId

class SongResponseModel(BaseModel):
    id: ObjectId
    name: str
    artists: List[str]
    url: str
    thumbnail: str
    source: str
    playlists: List[str]
    distance: float
