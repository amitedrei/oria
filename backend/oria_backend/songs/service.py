from typing import List

from oria_backend.data_transformers.models import UploadPost
from oria_backend.data_transformers.route import get_song_for_post_data
from oria_backend.songs.models import SongResponseModel
from oria_backend.songs.mongo import mongodb
from bson import ObjectId


async def get_all_songs() -> List[SongResponseModel]:
    songs = await mongodb.get_all_songs()
    return [
        SongResponseModel(
            id=str(song["_id"]),
            song_id=song["song_id"],
            name=song["name"],
            artists=song["artists"],
            url=song["url"],
            thumbnail=song["thumbnail"],
            source=song["source"],
            playlists=song["playlists"],
            distance=-1,
        )
        for song in songs
    ]


async def find_top_songs(data: UploadPost) -> List[SongResponseModel]:
    song_data = await get_song_for_post_data(data.text, data.image)
    description_embedding = song_data[0]
    emotions_embedding = song_data[1]
    similar_songs = await mongodb.find_similar_songs(description_embedding=description_embedding,
                                                     emotions_embedding=emotions_embedding,
                                                     n=5
                                                     )
    


    return [
        SongResponseModel(
            id=str(song["_id"]),
            song_id=song['song_id'],
            name=song["name"],
            artists=song["artists"],
            url=song["url"],
            thumbnail=song["thumbnail"],
            source=song["source"],
            playlists=song["playlists"],
            distance=song["chorus_distance"],
        )
        for song in similar_songs
    ]
