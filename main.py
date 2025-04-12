from fastapi import FastAPI
from routers import auth
from database import register_lifespan_events

app = FastAPI()
register_lifespan_events(app)
app.include_router(auth.router)

