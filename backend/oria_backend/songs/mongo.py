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
        description_weight: float = 0.6
    ) -> List[Dict[str, Any]]:
        
        if not (0 <= description_weight <= 1):
            ValueError('description_weight must be a float in [0, 1]')
        
        if emotions_embedding is not None:
            description_weight = 1

        emotion_weight = 1 - description_weight
        
        all_songs = await self.get_all_songs()
        
        for song in all_songs:
            desc_distance = np.linalg.norm(
                np.array(description_embedding) - np.array(song["chorus_embedding"])
            )

            if emotion_weight:
                emotion_distance = np.linalg.norm(
                    np.array(emotions_embedding) - np.array(song["emotion_embedding"])
                )
            else:
                emotion_distance = 0
            
            song["distance"] = (description_weight * desc_distance + 
                            emotion_weight * emotion_distance)
        
        return sorted(all_songs, key=lambda x: x["distance"])[:max(n, len(all_songs))]

    async def close(self):
        await self.client.close()


mongodb = MongoDB()
