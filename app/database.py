# app/database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import certifi

load_dotenv()

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database():
    return db.database

async def connect_to_mongo():
    try:
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            print("Warning: MONGODB_URL not found in environment variables")
            return
        
        # Provide CA bundle for TLS verification (fixes CERTIFICATE_VERIFY_FAILED on macOS)
        db.client = AsyncIOMotorClient(mongodb_url, tlsCAFile=certifi.where())
        db.database = db.client.financial_app
        
        # Test the connection
        await db.client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
        
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")