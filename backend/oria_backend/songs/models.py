from pydantic import BaseModel


class SongResponseModel(BaseModel):
    id: str
    name: str
    artists: list[str]
    url: str
    source: str
    playlists: list[str]
    distance: float = -1
    thumbnail: str
    percentage: float = 0.0
    song_embedding: list[float] | None = None


class TopSongResponseModel(BaseModel):
    songs: list[SongResponseModel]
    post_embedding: list[float]


class LikeSongRequestModel(BaseModel):
    song_id: str
    post_embedding: list[float]
    song_embedding: list[float]
