from typing import Any, Dict, List

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
        self.songs_collection = self.db.song_v4

    def __del__(self):
        self.close()

    async def get_all_songs(self) -> List[Dict[str, Any]]:
        cursor = self.songs_collection.find()
        return await cursor.to_list(length=None)

    def close(self):
        self.client.close()


mongodb = MongoDB()
