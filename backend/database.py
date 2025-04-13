import os
from dotenv import load_dotenv, find_dotenv
from databases import Database
from fastapi import FastAPI

load_dotenv(find_dotenv("key.env"))

DATABASE_URL = os.getenv("DATABASE_URL")
database = Database(DATABASE_URL)

async def init_db():
    """Initialize database tables and columns"""
    await database.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            query_id UUID PRIMARY KEY,
            user_id VARCHAR NOT NULL,
            query_text TEXT NOT NULL,
            refined_query TEXT,
            status VARCHAR NOT NULL,
            web_sources JSONB DEFAULT '[]'::jsonb,
            twitter_sources JSONB DEFAULT '[]'::jsonb,
            final_sources JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def register_lifespan_events(app: FastAPI):
    @app.on_event("startup")
    async def startup():
        await database.connect()
        await init_db()

    @app.on_event("shutdown")
    async def shutdown():
        await database.disconnect()
