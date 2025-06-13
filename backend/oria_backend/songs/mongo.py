from typing import Any, Dict, List, Optional
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
from oria_backend.config import settings
from sklearn.neighbors import NearestNeighbors

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
        self.songs_collection = self.db.songs_v5
        self.__mood_embeddings = []
        self.__chorus_embeddings = []
        self.__name_embeddings = []
        self.__labels = []
        self.__max_object_id = 0
        self.__count = 0
        self.__changed = True

    async def __get_cache_signature(self):
        pipeline = [
            {"$group": {
                "_id": None,
                "count": {"$sum": 1},
                "max_id": {"$max": "$_id"}
            }}
        ]

        result = await self.songs_collection.aggregate(pipeline).to_list(length=None)
        if result:
            return result[0]["count"], result[0]["max_id"]
        return 0, None

    async def get_all_songs(self) -> List[Dict[str, Any]]:
        count, max_object_id = await self.__get_cache_signature()
        if count == self.__count and max_object_id == self.__max_object_id and len(self.__mood_embeddings):
            return self.__mood_embeddings, self.__chorus_embeddings, self.__name_embeddings, self.__labels

        self.__changed = True
        self.__count = count
        self.__max_object_id = max_object_id

        songs_cursor = self.songs_collection.find({})

        mood_embeddings = []
        chorus_embeddings = []
        name_embeddings = []
        labels = []

        # Use async for instead of regular for
        async for song in songs_cursor:
            mood_embeddings.append(song["mood_embedding"])
            chorus_embeddings.append(song["chorus_embedding"])
            name_embeddings.append(song["name_embedding"])
            labels.append((song.get("id", ""), song.get("name", ""), song.get("artists", ""), song.get("source", ""), song.get("url", "")))

        self.__mood_embeddings = np.array(mood_embeddings, dtype=np.float32)
        self.__chorus_embeddings = np.array(chorus_embeddings, dtype=np.float32)
        self.__name_embeddings = np.array(name_embeddings, dtype=np.float32)
        self.__labels = labels

        return self.__mood_embeddings, self.__chorus_embeddings, self.__name_embeddings, self.__labels

    async def close(self):
        await self.client.close()

    def is_changed(self):
        return self.__changed


mongodb = MongoDB()
