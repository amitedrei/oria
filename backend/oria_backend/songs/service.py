from typing import Any, List

from fastapi import UploadFile
from oria_backend.data_transformers.service import (
    extract_description_from_image,
    get_embeddings,
)
from oria_backend.songs.models import SongResponseModel
from oria_backend.songs.mongo import mongodb
from oria_backend.utils import get_n_closest_embedding_documents

SONGS_FILTER_AMOUNTS = [20, 10, 5]
NAME_EMBEDDING_FIELD = "name_embedding"
LYRICS_EMBEDDING_FIELD = "lyrics_embedding"
TOP_SONGS_AMOUNT = 5


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
            distances={},
        )
        for song in songs
    ]


def find_top_songs_by_name(
    songs: list[dict[str, Any]],
    image_description: str,
    caption: str,
    n: int,
    query_embedding: list[float] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    if query_embedding is None:
        combined_query = f"{image_description}. Caption: {caption}"
        query_embedding = get_embeddings(combined_query)

    distance_field, closest_documents = get_n_closest_embedding_documents(
        songs, query_embedding, embedding_field=NAME_EMBEDDING_FIELD
    )

    return distance_field, closest_documents[:n]


def find_top_songs_by_lyrics(
    songs: list[dict[str, Any]],
    image_description: str,
    caption: str,
    n: int,
    query_embedding: list[float] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    if query_embedding is None:
        combined_query = f"{image_description}. Caption: {caption}"
        query_embedding = get_embeddings(combined_query)

    distance_field, closest_documents = get_n_closest_embedding_documents(
        songs, query_embedding, embedding_field=LYRICS_EMBEDDING_FIELD
    )

    return distance_field, closest_documents[:n]


async def find_top_songs(image: UploadFile, caption: str) -> List[SongResponseModel]:
    top_songs = await mongodb.get_all_songs()
    distance_fields: list[str] = []

    image_description = extract_description_from_image(image)

    for i, song_filter in enumerate([find_top_songs_by_name, find_top_songs_by_lyrics]):
        distance_field, top_songs = song_filter(
            top_songs, image_description, caption, SONGS_FILTER_AMOUNTS[i]
        )
        distance_fields.append(distance_field)

    return [
        SongResponseModel(
            id=song["_id"],
            name=song["name"],
            artists=song["artists"],
            url=song["url"],
            thumbnail=song["thumbnail"],
            source=song["source"],
            playlists=song["playlists"],
            distances={field: song[field] for field in distance_fields},
            distance=sum(song[field] for field in distance_fields if field in song)
            / len(distance_fields)
            if distance_fields
            else -1,
        )
        for song in top_songs[:TOP_SONGS_AMOUNT]
    ]
