from typing import Any, Dict, List, Optional
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
        self.songs_collection = self.db.songs_v2

    async def get_all_songs(self) -> List[Dict[str, Any]]:
        cursor = self.songs_collection.find()
        return await cursor.to_list(length=None)

    async def find_similar_songs(
        self, 
        description_embedding: List[float], 
        emotions_embedding: Optional[List[float]] = None,
        n: Optional[int] = 5,
    ) -> List[Dict[str, Any]]:
        
        if not emotions_embedding:
            emotions_embedding = description_embedding

        all_songs = await self.get_all_songs()

        emotions_embedding_np = np.array(emotions_embedding)
        description_embedding_np = np.array(description_embedding)

        for song in all_songs:
            song['emotion_distance'] = np.linalg.norm(
            emotions_embedding_np - np.array(song["mood_embedding"])
        )

        sorted_songs = sorted(all_songs, key=lambda x: x['emotion_distance'])[:min(n*20, len(all_songs))]
        
        for song in sorted_songs:
            song['chorus_distance'] = np.linalg.norm(
                description_embedding_np - np.array(song['chorus_embedding'])
            )      

        return sorted(sorted_songs, key=lambda x: x["chorus_distance"])[:min(n, len(sorted_songs))]

    async def close(self):
        await self.client.close()


mongodb = MongoDB()
