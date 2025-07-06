from beanie import Document, Indexed
from typing import List, Set, Optional
from pydantic import Field, ConfigDict
from pymongo import IndexModel
from bson import ObjectId

class Song(Document):
    id: ObjectId = Field(default_factory=lambda: ObjectId(), primary_field=True)
    song_id: str
    source: str
    name: str
    sname: str
    artists: List[str]
    url: str
    thumbnail: str
    playlists: Set[str]
    name_embedding: List[float]
    chorus: str
    chorus_embedding: List[float]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    class Settings:
        name = "songs_v5"
        indexes = [
            IndexModel(
                [("song_id"), ("source")],
                unique=True
            ),
            IndexModel(
                [("url")],
                unique=True
            )
        ]

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_playlists

    @classmethod
    def validate_playlists(cls, v):
        if not isinstance(v, set):
            return set(v)

        return v