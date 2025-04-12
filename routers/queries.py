from fastapi import APIRouter, Request, HTTPException
from database import database
from jose import jwt
import os
from uuid import UUID 
import uuid 

router = APIRouter(prefix="/queries", tags=["queries"])

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

@router.post("")
async def create_query(data: dict, request: Request):
    user_id = get_current_user(request)
    query_id = str(uuid.uuid4())
    initial_query = data.get("initial_query")

    if not initial_query:
        raise HTTPException(status_code=400, detail="initial_query is required")

    insert_query = """
    INSERT INTO queries (query_id, user_id, initial_query, status, created_at)
    VALUES (:query_id, :user_id, :initial_query, 'pending', NOW())
    """

    await database.execute(insert_query, {
        "query_id": query_id,
        "user_id": user_id,
        "initial_query": initial_query
    })

    return {"query_id": query_id, "status": "pending"}

@router.get("/all")
async def list_user_queries(request: Request):
    user_id = get_current_user(request)

    rows = await database.fetch_all("""
        SELECT query_id, initial_query, refined_query, status, created_at
        FROM queries
        WHERE user_id = :user_id
        ORDER BY created_at DESC
    """, {"user_id": user_id})

    return [dict(row) for row in rows]

@router.get("/{query_id}")
async def get_query(query_id: str, request: Request):
    user_id = get_current_user(request)

    query = await database.fetch_one("""
        SELECT query_id, initial_query, refined_query, status, created_at
        FROM queries
        WHERE query_id = :query_id AND user_id = :user_id
    """, {"query_id": query_id, "user_id": user_id})

    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    return dict(query)

@router.post("/{query_id}/accept")
async def accept_query(query_id: str, request: Request):
    user_id = get_current_user(request)

    update_query = """
    UPDATE queries SET status = 'accepted'
    WHERE query_id = :query_id AND user_id = :user_id
    """

    await database.execute(update_query, {
        "query_id": query_id,
        "user_id": user_id
    })

    return {"message": "Query marked as accepted"}

@router.post("/{query_id}/reject")
async def reject_query(query_id: str, request: Request):
    user_id = get_current_user(request)

    update_query = """
    UPDATE queries SET status = 'rejected'
    WHERE query_id = :query_id AND user_id = :user_id
    """

    await database.execute(update_query, {
        "query_id": query_id,
        "user_id": user_id
    })

    return {"message": "Query marked as rejected"}


#refine given query based on given feedback 

@router.post("/{query_id}/refine")
async def start_refinement(query_id: str, data: dict, request: Request):
    user_id = get_current_user(request)

    # fetch user profile from DB
    row = await database.fetch_one("""
        SELECT archetype, user_description, user_goals, user_experience
        FROM users
        WHERE user_id = :user_id
    """, {"user_id": user_id})

    if not row:
        raise HTTPException(status_code=404, detail="User profile not found")

    background_data = {
        "user_type": row["archetype"] or "Unknown",
        "research_purpose": row["user_goals"] or "Unknown",
        "user_description": row["user_description"] or "Unknown",
        "query_frequency": "weekly"
    }

    current_query = data.get("query")

    if not current_query:
        raise HTTPException(status_code=400, detail="Missing query")

    request_obj = QueryRequest(query=current_query, background=UserBackground(**background_data))
    response = await run_refinement(request_obj)
    return response.dict()
