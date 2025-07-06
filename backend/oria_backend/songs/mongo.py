from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorClient
from oria_backend.utils import timed_cache
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
        self.songs_collection = self.db.songs_v5

    def __del__(self):
        self.close()

    @timed_cache(ttl_seconds=300)
    async def get_all_songs(
        self, count: int | None = None, projection: dict | None = None
    ) -> List[Dict[str, Any]]:
        cursor = self.songs_collection.find(projection=projection)
        if count is not None:
            cursor = cursor.limit(count)
        return await cursor.to_list(length=None)

    async def update_song(self, song_id: str, update_data: Dict[str, Any]) -> None:
        await self.songs_collection.update_one({"_id": song_id}, {"$set": update_data})

    def close(self):
        self.client.close()


mongodb = MongoDB()
