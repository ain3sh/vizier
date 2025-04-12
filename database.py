import os
from dotenv import load_dotenv
from databases import Database
from fastapi import FastAPI

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
database = Database(DATABASE_URL)

def register_lifespan_events(app: FastAPI):
    @app.on_event("startup")
    async def startup():
        await database.connect()

    @app.on_event("shutdown")
    async def shutdown():
        await database.disconnect()
