from fastapi import FastAPI
from routers import auth, user, queries
from database import register_lifespan_events

app = FastAPI()
register_lifespan_events(app)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(queries.router)

