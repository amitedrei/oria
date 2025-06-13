from typing import List

from pydantic import BaseModel

class SongResponseModel(BaseModel):
    id: str
    name: str
    artists: List[str]
    url: str
    source: str
    percentage: float
