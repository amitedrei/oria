from beanie import Document, Indexed
from typing import List, Set, Optional
from pydantic import Field


class Song(Document):
    id: str
    source: str
    name: str
    artists: List[str]
    url: Indexed(str, unique=True)  # URL still unique
    thumbnail: str
    embedding: List[float]
    playlists: Set[str]


    class Settings:
        name = "songs"
        indexes = [
            [("id", 1), ("source", 1)],  # Compound index for id+source uniqueness
        ]

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_playlists

    @classmethod
    def validate_playlists(cls, v):
        if v is None:
            return set()
        return v