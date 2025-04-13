from typing import List

from oria_backend.data_transformers.models import UploadPost
from oria_backend.data_transformers.route import get_song_for_post_data
from oria_backend.songs.models import SongResponseModel
from oria_backend.songs.mongo import mongodb


async def get_all_songs() -> List[SongResponseModel]:
    songs = await mongodb.get_all_songs()
    return [
        SongResponseModel(
            id=song["_id"],
            name=song["name"],
            artists=song["artists"],
            url=song["url"],
            thumbnail=song["thumbnail"],
            source=song["source"],
            playlists=song["playlists"],
            distance=song["distance"],
        )
        for song in songs
    ]


async def find_top_songs(data: UploadPost) -> List[SongResponseModel]:
    song_data = await get_song_for_post_data(data)
    embedding = song_data.embeddings
    similar_songs = await mongodb.find_similar_songs(embedding, 5)

    return [
        SongResponseModel(
            id=song["_id"],
            name=song["name"],
            artists=song["artists"],
            url=song["url"],
            thumbnail=song["thumbnail"],
            source=song["source"],
            playlists=song["playlists"],
            distance=song["distance"],
        )
        for song in similar_songs
    ]
