from fastapi import APIRouter, Request, HTTPException
from database import database
from jose import jwt
import os
from uuid import UUID 
import uuid 
from refiner import UserBackground, QueryRequest, QueryResponse, refine_query as run_refinement
import json
import collections, re

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

    # step 1: create a new source_set with 3 empty template sources
    source_set_id = str(uuid.uuid4())
    template_sources = [
        {
            "id": str(uuid.uuid4()),
            "name": f"name{i}",
            "title": f"title{i}",
            "url": f"url{i}.com/{i}",
            "date": f"date{i}",
            "author": f"author{i}",
            "snippet": f"snippet",
            "root": f"{i}.com"
        } for i in range(3)
    ]

    insert_source_set = """
    INSERT INTO source_sets (source_set_id, sources)
    VALUES (:source_set_id, :sources)
    """
    await database.execute(insert_source_set, {
        "source_set_id": source_set_id,
        "sources": json.dumps(template_sources)
    })

    # step 2: insert the query and associate the source_set
    insert_query = """
    INSERT INTO queries (query_id, user_id, initial_query, source_set_id, status, created_at)
    VALUES (:query_id, :user_id, :initial_query, :source_set_id, 'pending', NOW())
    """
    await database.execute(insert_query, {
        "query_id": query_id,
        "user_id": user_id,
        "initial_query": initial_query,
        "source_set_id": source_set_id
    })

    return {"query_id": query_id, "source_set_id": source_set_id, "status": "pending"}


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

#return the source list for that query id
@router.get("/{query_id}/sources")
async def get_query_sources(query_id: str, request: Request):
    user_id = get_current_user(request)

    row = await database.fetch_one("""
        SELECT s.sources
        FROM queries q
        JOIN source_sets s ON q.source_set_id = s.source_set_id
        WHERE q.query_id = :query_id AND q.user_id = :user_id
    """, {
        "query_id": query_id,
        "user_id": user_id
    })

    if not row:
        raise HTTPException(status_code=404, detail="No sources found")

    return row["sources"]

#at@router.post("/{query_id}/attach-source-set")
async def attach_source_set(query_id: str, data: dict, request: Request):
    user_id = get_current_user(request)
    source_set_id = data.get("source_set_id")

    if not source_set_id:
        raise HTTPException(status_code=400, detail="Missing source_set_id")

    # update query to point to new source set
    await database.execute("""
        UPDATE queries
        SET source_set_id = :source_set_id
        WHERE query_id = :query_id AND user_id = :user_id
    """, {
        "source_set_id": source_set_id,
        "query_id": query_id,
        "user_id": user_id
    })

    # fetch sources json from source_sets
    row = await database.fetch_one("""
        SELECT sources FROM source_sets
        WHERE source_set_id = :source_set_id
    """, {"source_set_id": source_set_id})

    if not row or not row["sources"]:
        raise HTTPException(status_code=404, detail="Source set not found")

    # parse the JSON string
    try:
        sources = json.loads(row["sources"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing sources: {str(e)}")

    # extract and normalize roots
    roots = []
    for source in sources:
        root = source.get("root")
        if not root:
            continue
        if root.startswith("https://x.com/"):
            root = "@" + root.replace("https://x.com/", "").split("/")[0]
        roots.append(root.lower())

    # count frequency and get top 3
    counter = collections.Counter(roots)
    top_roots = [r for r, _ in counter.most_common()]

    # update query with top_source_roots
    await database.execute("""
        UPDATE queries
        SET top_source_roots = :top_roots
        WHERE query_id = :query_id
    """, {
        "top_roots": top_roots,
        "query_id": query_id
    })

    return {
        "message": "✅ source_set attached and top_source_roots saved",
        "top_roots": top_roots
    }

#create new source-set 
@router.post("/source-sets")
async def create_source_set(data: dict, request: Request):
    user_id = get_current_user(request)
    source_set_id = str(uuid.uuid4())
    sources = data.get("sources")

    if not isinstance(sources, list):
        raise HTTPException(status_code=400, detail="sources must be a list of objects")

    insert_query = """
    INSERT INTO source_sets (source_set_id, sources)
    VALUES (:source_set_id, :sources)
    """

    await database.execute(insert_query, {
        "source_set_id": source_set_id,
        "sources": json.dumps(sources)
    })

    return {"source_set_id": source_set_id}


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

    # request_obj = QueryRequest(query=current_query, background=UserBackground(**background_data))
    # response = await run_refinement(request_obj)

    dummy_refined = f"🧠 This is a Refined version of: {current_query}"

    await database.execute("""
        UPDATE queries SET refined_query = :refined_query
        WHERE query_id = :query_id AND user_id = :user_id
    """, {
        "refined_query": dummy_refined, #response.refined_query,
        "query_id": query_id,
        "user_id": user_id
    })

    return {"refined_query": dummy_refined} #response.refined_query