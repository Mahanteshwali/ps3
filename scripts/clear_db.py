import asyncio
import os
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017/threatdb")
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:16379")
STREAM_NAME = os.getenv("REDIS_STREAM", "threat-events")

async def clear_db():
    print(f"🧹 Clearing databases...")
    
    # Clear MongoDB
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client.get_default_database()
        
        # Delete all alerts and logs
        res_alerts = await db["alerts"].delete_many({})
        res_logs = await db["logs"].delete_many({})
        
        print(f"✅ MongoDB: Deleted {res_alerts.deleted_count} alerts and {res_logs.deleted_count} logs.")
        client.close()
    except Exception as e:
        print(f"❌ MongoDB error: {e}")

    # Clear Redis Stream
    try:
        r = await aioredis.from_url(REDIS_URL, decode_responses=True)
        # Delete the stream key
        await r.delete(STREAM_NAME)
        print(f"✅ Redis: Deleted stream '{STREAM_NAME}'.")
        await r.aclose()
    except Exception as e:
        print(f"❌ Redis error: {e}")

    print("✨ Database reset complete.")

if __name__ == "__main__":
    asyncio.run(clear_db())
