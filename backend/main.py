from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from routers import auth, user, queries, drafts
from database import register_lifespan_events

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

# Global process state tracker
process_states = {}

register_lifespan_events(app)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(queries.router)
app.include_router(drafts.router)
