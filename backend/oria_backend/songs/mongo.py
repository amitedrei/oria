from typing import Any, Dict, List

import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
from oria_backend.config import settings


class MongoDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(
            settings.mongo_uri,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
            ssl=True,
        )
        self.db = self.client[settings.mongo_db_name]
        self.songs_collection = self.db.songs

    async def get_all_songs(self) -> List[Dict[str, Any]]:
        cursor = self.songs_collection.find()
        return await cursor.to_list(length=None)

    async def find_similar_songs(
        self, embedding: List[float], n: int
    ) -> List[Dict[str, Any]]:
        all_songs = await self.get_all_songs()
        for song in all_songs:
            song["distance"] = np.linalg.norm(
                np.array(embedding) - np.array(song["embedding"])
            )
        return sorted(all_songs, key=lambda x: x["distance"])[:n]

    async def close(self):
        await self.client.close()


mongodb = MongoDB()
