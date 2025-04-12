from fastapi import APIRouter, Request, HTTPException
from database import database
from jose import jwt
import os
import uuid
from uuid import UUID
import json

router = APIRouter(prefix="/drafts", tags=["drafts"])

JWT_SECRET = os.getenv("JWT_SECRET")

def get_current_user(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return UUID(payload["sub"])
    except Exception as e:
        print("❌ Invalid token:", e)
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/generate")
async def generate_draft(data: dict, request: Request):
    user_id = get_current_user(request)
    query_id = data.get("query_id")

    if not query_id:
        raise HTTPException(status_code=400, detail="query_id is required")

    # 🔍 fetch source_set_id from query
    source_row = await database.fetch_one("""
        SELECT q.source_set_id, s.sources
        FROM queries q
        JOIN source_sets s ON q.source_set_id = s.source_set_id
        WHERE q.query_id = :query_id AND q.user_id = :user_id
    """, {
        "query_id": query_id,
        "user_id": user_id
    })

    if not source_row:
        raise HTTPException(status_code=404, detail="No sources found for this query")

    source_set_id = source_row["source_set_id"]

    draft_id = str(uuid.uuid4())
    dummy_content = f"This is a draft summary for query {query_id}."

    insert_query = """
    INSERT INTO drafts (draft_id, query_id, user_id, source_set_id, content, status, created_at)
    VALUES (:draft_id, :query_id, :user_id, :source_set_id, :content, 'generated', NOW())
    """

    await database.execute(insert_query, {
        "draft_id": draft_id,
        "query_id": query_id,
        "user_id": user_id,
        "source_set_id": source_set_id,
        "content": dummy_content
    })

    return {"draft_id": draft_id, "status": "generated"}

@router.post("/accept")
async def accept_draft(data: dict, request: Request):
    user_id = get_current_user(request)
    draft_id = data.get("draft_id")

    if not draft_id:
        raise HTTPException(status_code=400, detail="draft_id is required")

    update_query = """
    UPDATE drafts SET status = 'accepted'
    WHERE draft_id = :draft_id AND user_id = :user_id
    """

    await database.execute(update_query, {
        "draft_id": draft_id,
        "user_id": user_id
    })

    return {"message": "Draft accepted", "draft_id": draft_id}

@router.post("/reject")
async def reject_draft(data: dict, request: Request):
    user_id = get_current_user(request)
    draft_id = data.get("draft_id")

    if not draft_id:
        raise HTTPException(status_code=400, detail="draft_id is required")

    update_query = """
    UPDATE drafts SET status = 'rejected'
    WHERE draft_id = :draft_id AND user_id = :user_id
    """

    await database.execute(update_query, {
        "draft_id": draft_id,
        "user_id": user_id
    })

    return {"message": "Draft rejected", "draft_id": draft_id}
