from typing import Any
from bson import ObjectId
from loguru import logger
from fastapi import UploadFile
import numpy as np
from oria_backend.data_transformers.service import (
    extract_description_from_image,
    get_embeddings,
    get_image_from_upload_file,
)
from oria_backend.utils import normalize_vector, timed_cache
from oria_backend.songs.models import (
    LikeSongRequestModel,
    SongResponseModel,
    TopSongResponseModel,
)
from oria_backend.songs.mongo import mongodb

NAME_EMBEDDING_FIELD = "name_embedding"
CHORUS_EMBEDDING_FIELD = "chorus_embedding"
POSTS_EMBEDDING_FIELD = "posts_embeddings"
SONG_EMBEDDING_FIELD = "song_embedding"
POST_DISTANCE_FIELD = "posts_distance"
TOP_SONGS_AMOUNT = 5


SONG_NAME_WEIGHT = 0.9
CHORUS_WEIGHT = 0.1
POST_EMBEDDING_WEIGHT = 0.1
SONG_EMBEDDING_WEIGHT = 0.9


@timed_cache(ttl_seconds=300)
async def get_all_songs(count):
    labels = await mongodb.get_all_songs(
        count,
        projection={
            "_id": 1,
            "name": 1,
            "artists": 1,
            "url": 1,
            "source": 1,
            "thumbnail": 1,
            "playlists": 1,
        },
    )
    songs = []
    for label in labels:
        songs.append(
            SongResponseModel(
                id=str(label["_id"]),
                name=label["name"],
                artists=label["artists"],
                url=label["url"],
                source=label["source"],
                thumbnail=label["thumbnail"],
                distance=-1,
                playlists=label.get("playlists", []),
            )
        )

    return songs


def get_n_closest_songs(
    songs_documents: list[dict[str, Any]], post_embedding: list[float]
):
    normalized_post_embedding = normalize_vector(post_embedding)

    for song in songs_documents:
        name_embeddings = normalize_vector(song[NAME_EMBEDDING_FIELD])
        chorus_embeddings = normalize_vector(song[CHORUS_EMBEDDING_FIELD])
        song_embedding = (
            name_embeddings * SONG_NAME_WEIGHT + chorus_embeddings * CHORUS_WEIGHT
        )
        song_embedding = normalize_vector(song_embedding)

        song_posts_embeddings = song.get(POSTS_EMBEDDING_FIELD, [])
        normalized_posts_embeddings = []
        for post_emb in song_posts_embeddings:
            post_emb = normalize_vector(post_emb)
            new_song_emb = (
                post_emb * POST_EMBEDDING_WEIGHT
                + song_embedding * SONG_EMBEDDING_WEIGHT
            )
            new_song_emb = normalize_vector(new_song_emb)
            normalized_posts_embeddings.append(new_song_emb)

        cosine_similarities = [
            np.dot(song_post_embedding, normalized_post_embedding)
            / (
                np.linalg.norm(song_post_embedding)
                * np.linalg.norm(normalized_post_embedding)
            )
            for song_post_embedding in normalized_posts_embeddings
        ]
        cosine_similarities.append(
            np.dot(song_embedding, normalized_post_embedding)
            / (
                np.linalg.norm(song_embedding)
                * np.linalg.norm(normalized_post_embedding)
            )
        )
        song[POST_DISTANCE_FIELD] = max(cosine_similarities)
        song[SONG_EMBEDDING_FIELD] = song_embedding
    return sorted(songs_documents, key=lambda x: x[POST_DISTANCE_FIELD], reverse=True)


async def find_top_songs(image: UploadFile, caption: str) -> TopSongResponseModel:
    all_songs = await mongodb.get_all_songs(
        projection={
            NAME_EMBEDDING_FIELD: 1,
            CHORUS_EMBEDDING_FIELD: 1,
            POSTS_EMBEDDING_FIELD: 1,
            "name": 1,
            "artists": 1,
            "url": 1,
            "thumbnail": 1,
            "source": 1,
            "playlists": 1,
        }
    )
    image_obj = get_image_from_upload_file(image)
    image_description = extract_description_from_image(image_obj)
    image_embedding = get_embeddings(image_description)

    image_embedding = np.array(image_embedding)
    image_embedding = image_embedding / np.linalg.norm(image_embedding)

    if len(caption) > 0:
        caption_embedding = get_embeddings(caption)

        caption_embedding = np.array(caption_embedding)
        caption_embedding = caption_embedding / np.linalg.norm(caption_embedding)

        caption_weight = 0.3
        combined_embeddings = caption_embedding * caption_weight + image_embedding * (
            1 - caption_weight
        )
        combined_embeddings = combined_embeddings / np.linalg.norm(combined_embeddings)
        combined_embeddings = combined_embeddings.tolist()
    else:
        combined_embeddings = image_embedding.tolist()

    logger.info(f'Image description: "{image_description}"')
    logger.info(f'Caption: "{caption}"')

    top_songs = get_n_closest_songs(all_songs, combined_embeddings)

    top_songs = sorted(
        [
            SongResponseModel(
                id=str(song["_id"]),
                name=song["name"],
                artists=song["artists"],
                url=song["url"],
                thumbnail=song["thumbnail"],
                source=song["source"],
                playlists=song["playlists"],
                distance=song[POST_DISTANCE_FIELD],
                percentage=song[POST_DISTANCE_FIELD],
                song_embedding=song[SONG_EMBEDDING_FIELD],
            )
            for song in top_songs
        ],
        key=lambda x: x.distance,
        reverse=True,
    )[:TOP_SONGS_AMOUNT]

    return TopSongResponseModel(
        songs=top_songs,
        post_embedding=combined_embeddings,
    )


async def like_song(data: LikeSongRequestModel) -> None:
    await mongodb.songs_collection.update_one(
        {"_id": ObjectId(data.song_id)},
        {
            "$push": {
                POSTS_EMBEDDING_FIELD: {
                    "$each": [data.post_embedding],
                }
            }
        },
    )
