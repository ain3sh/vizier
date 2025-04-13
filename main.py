from fastapi import FastAPI
from routers import auth, user, queries,drafts
from database import register_lifespan_events

from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,  # required for cookies/auth headers
    allow_methods=["*"],
    allow_headers=["*"],     # includes Authorization
)

register_lifespan_events(app)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(queries.router)
app.include_router(drafts.router)
