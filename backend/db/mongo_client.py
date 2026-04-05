"""
MongoDB async client using Motor.
"""
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db():
    global _client, _db
    url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "threatdb")
    _client = AsyncIOMotorClient(url)
    _db = _client[db_name]
    # Create indexes for common query patterns
    await _db["alerts"].create_index([("created_at", -1)])
    await _db["alerts"].create_index([("severity", 1)])
    await _db["alerts"].create_index([("threat_type", 1)])
    await _db["logs"].create_index([("timestamp", -1)])
    await _db["logs"].create_index([("layer", 1)])
    logger.info(f"Connected to MongoDB: {url}/{db_name}")


async def close_db():
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return _db
