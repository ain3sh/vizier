from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from uuid import uuid4

app = FastAPI()

# Allow CORS for local frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dummy Auth Dependency
def get_current_user():
    return "dummy-user-id"

# Routers
auth_router = APIRouter(prefix="/auth", tags=["auth"])
user_router = APIRouter(prefix="/user", tags=["user"])
query_router = APIRouter(prefix="/queries", tags=["queries"])
draft_router = APIRouter(prefix="/drafts", tags=["drafts"])
publish_router = APIRouter(prefix="/publish", tags=["publish"])

# ===== AUTH ROUTES =====
@auth_router.get("/callback")
def auth_callback(code: str):
    return {"access_token": "dummy.jwt.token.from.google"}

@auth_router.get("/me")
def auth_me(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}

# ===== USER ROUTES =====
@user_router.get("/me")
def get_user_profile(user_id: str = Depends(get_current_user)):
    return {
        "name": "user full name",
        "email": "user@example.com",
        "archetype": "Researcher",
        "user_experience": 7
    }

@user_router.post("/profile")
def update_user_profile(data: dict, user_id: str = Depends(get_current_user)):
    return {"message": "Profile updated", "data": data}

# ===== QUERY ROUTES =====
@query_router.get("/")
def get_queries(user_id: str = Depends(get_current_user)):
    return [{"query_id": str(uuid4()), "initial_query": "What's happening in AI?"}]

@query_router.post("/")
def submit_query(data: dict, user_id: str = Depends(get_current_user)):
    return {"query_id": str(uuid4())}

# ===== DRAFT ROUTES =====
@draft_router.post("/generate")
def generate_draft(data: dict, user_id: str = Depends(get_current_user)):
    return {"draft_id": str(uuid4()), "status": "pending"}

@draft_router.get("/{draft_id}")
def get_draft_by_id(draft_id: str, user_id: str = Depends(get_current_user)):
    return {
        "draft_id": draft_id,
        "content": "AI is evolving rapidly.",
        "status": "accepted",
        "sources": ["source1", "source2"],
        "generated_at": "2024-04-12T15:30:00Z"
    }

@draft_router.post("/accept")
def accept_draft(data: dict, user_id: str = Depends(get_current_user)):
    return {"message": "Draft accepted"}

@draft_router.post("/reject")
def reject_draft(data: dict, user_id: str = Depends(get_current_user)):
    return {"message": "Draft rejected"}

# ===== PUBLISH/SHARE ROUTES =====
@publish_router.post("/{draft_id}")
def publish_draft(draft_id: str, user_id: str = Depends(get_current_user)):
    return {
        "public_id": "abc123xyz",
        "share_url": f"http://localhost:8000/share/abc123xyz"
    }

@app.get("/share/{public_id}")
def get_public_draft(public_id: str):
    return {"content": "This is a public draft.", "sources": ["source1", "source2"]}

# Register routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(query_router)
app.include_router(draft_router)
app.include_router(publish_router)
