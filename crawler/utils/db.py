from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.song import Song

async def init_database(connection_string, db_name="music_data"):
    client = AsyncIOMotorClient(connection_string)
    await init_beanie(database=client[db_name], document_models=[Song])
    return client[db_name]

async def close_database(client):
    """Close the database connection."""
    if client:
        client.close()