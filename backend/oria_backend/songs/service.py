from typing import Any, List
from loguru import logger
from fastapi import UploadFile
from oria_backend.data_transformers.service import (
    extract_description_from_image,
    get_embeddings,
    get_image_from_upload_file,
)
from oria_backend.songs.models import SongResponseModel
from oria_backend.songs.mongo import mongodb
from oria_backend.utils import get_n_closest_embedding_documents

NAME_EMBEDDING_FIELD = "name_embedding"
LYRICS_EMBEDDING_FIELD = "lyrics_embedding"
CHORUS_EMBEDDING_FIELD = "chorus_embedding"
TOP_SONGS_AMOUNT = 5
MAX_SONGS_CUT = 5


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


def build_field_distance_function(field: str, filter_category: str):
    def distance_function(
        songs: list[dict[str, Any]],
        n: int,
        query_embedding: list[float],
    ) -> tuple[str, list[dict[str, Any]]]:
        distance_field, closest_documents = get_n_closest_embedding_documents(
            songs,
            query_embedding,
            embedding_field=field,
            filter_category=filter_category,
        )

        return distance_field, closest_documents[:n]

    return distance_function


def get_top_songs_by_field(
    top_songs: list[dict[str, Any]],
    embedding: list[float],
    field: str,
    description: str,
    query_fields: list[str] = [
        NAME_EMBEDDING_FIELD,
        CHORUS_EMBEDDING_FIELD,
        LYRICS_EMBEDDING_FIELD,
    ],
) -> tuple[list[str], list[dict[str, Any]]]:
    distance_fields: list[str] = []
    logger.info(f'Quering by {field}: "{description}"')
    for i, song_filter_field in enumerate(query_fields):
        filter_function = build_field_distance_function(song_filter_field, field)
        cut_number = len(top_songs) // 2
        if cut_number > MAX_SONGS_CUT:
            cut_number = MAX_SONGS_CUT
        distance_field, top_songs = filter_function(
            top_songs,
            max(cut_number, TOP_SONGS_AMOUNT),
            embedding,
        )
        distance_fields.append(distance_field)

    logger.info(
        f"Top songs after filtering by {field}: {[(song['name'], [song[distance_field] for distance_field in distance_fields]) for song in top_songs]}"
    )

    return distance_fields, top_songs


async def find_top_songs(image: UploadFile, caption: str) -> List[SongResponseModel]:
    top_songs = await mongodb.get_all_songs()

    image_obj = get_image_from_upload_file(image)
    image_description = extract_description_from_image(image_obj)
    combined_description = f"'{image_description}'. Caption: '{caption}'"
    combined_embedding = get_embeddings(combined_description)
    image_embedding = get_embeddings(image_description)

    logger.info(f'Image description: "{image_description}"')
    logger.info(f'Caption: "{caption}"')

    combined_distance_fields, top_songs = get_top_songs_by_field(
        top_songs,
        combined_embedding,
        "combined",
        combined_description,
        query_fields=[
            NAME_EMBEDDING_FIELD,
        ],
    )

    image_chorus_distance_fields, top_songs = get_top_songs_by_field(
        top_songs,
        image_embedding,
        "image",
        image_description,
        query_fields=[
            CHORUS_EMBEDDING_FIELD,
        ],
    )

    distance_fields = combined_distance_fields + image_chorus_distance_fields

    return sorted(
        [
            SongResponseModel(
                id=str(song["_id"]),
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
            for song in top_songs
        ],
        key=lambda x: x.distance,
        reverse=True,
    )[:TOP_SONGS_AMOUNT]
