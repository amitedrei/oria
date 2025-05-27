from typing import List

from fastapi import UploadFile

from oria_backend.data_transformers.service import (
    extract_description_from_image,
    get_embeddings,
)
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
            distance=-1,
        )
        for song in songs
    ]


async def find_top_songs(image: UploadFile, caption: str) -> List[SongResponseModel]:
    image_description = extract_description_from_image(image)
    combined_query = f"{image_description}. Caption: {caption}"
    query_embedding = get_embeddings(combined_query)

    similar_songs = await mongodb.find_similar_songs(
        query_embedding, 5, document_embedding_field="name-embedding"
    )

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
