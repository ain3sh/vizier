from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from database import database
from jose import jwt
import os, uuid, json, asyncio
from uuid import UUID 
import collections, re
from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any, AsyncGenerator, List
from routers.openrouter import OpenRouterClient, get_openrouter_client
from datetime import datetime

router = APIRouter(prefix="/queries", tags=["queries"])

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable must be set")

class ProcessStage(str, Enum):
    QUERY_RECEIVED = "query_received"
    REFINEMENT_STARTED = "refinement_started" 
    REFINEMENT_COMPLETED = "refinement_completed"
    ROUTING_STARTED = "routing_started"
    ROUTING_COMPLETED = "routing_completed"
    WEB_SEARCH_STARTED = "web_search_started"
    WEB_SEARCH_COMPLETED = "web_search_completed"
    TWITTER_SEARCH_STARTED = "twitter_search_started" 
    TWITTER_SEARCH_COMPLETED = "twitter_search_completed"
    SOURCE_RERANK_STARTED = "source_rerank_started"
    SOURCE_RERANK_COMPLETED = "source_rerank_completed"
    SOURCE_REVIEW_READY = "source_review_ready"
    SOURCE_REVIEW_COMPLETED = "source_review_completed"
    WRITING_STARTED = "writing_started"
    DRAFT_READY = "draft_ready"
    DRAFT_APPROVED = "draft_approved"
    COMPLETED = "completed"

class SessionState:
    def __init__(self, query_id: str):
        self.query_id = query_id
        self.stage = ProcessStage.QUERY_RECEIVED
        self.is_completed = False
        self._event_queue = asyncio.Queue()
        
    async def update_stage(self, new_stage: ProcessStage, data: Optional[Dict] = None):
        event = {
            "stage": new_stage,
            "timestamp": str(uuid.uuid1()),
            "data": data or {}
        }
        await self._event_queue.put(event)
        self.stage = new_stage
        
        if new_stage == ProcessStage.COMPLETED:
            self.is_completed = True
            
    async def event_generator(self) -> AsyncGenerator[Dict, None]:
        while not self.is_completed or not self._event_queue.empty():
            try:
                event = await self._event_queue.get()
                yield event
            except Exception as e:
                print(f"Error in event generator: {e}")
                break

# Global session states
active_sessions: Dict[str, SessionState] = {}

async def get_current_user(request: Request) -> str:
    """Get authenticated user ID from JWT token"""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    try:
        token = auth.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

class SourceItem(BaseModel):
    """Source item with metadata"""
    url: str
    title: str
    content: str
    relevance_score: float
    source_type: str  # 'web' or 'twitter'
    timestamp: Optional[str]
    metadata: Dict[str, Any] = {}

class SourceReview(BaseModel):
    """User review of sources"""
    included: List[str]  # List of source URLs to include
    excluded: List[str]  # List of source URLs to exclude
    reranked_urls: List[str]  # Sources in desired order

@router.post("")
async def create_query(
    data: dict,
    request: Request,
    openrouter: OpenRouterClient = Depends(get_openrouter_client)
):
    """Create a new query"""
    user_id = await get_current_user(request)
    query_id = str(uuid.uuid4())
    
    try:
        await database.execute("""
            INSERT INTO queries (query_id, user_id, query_text, status)
            VALUES (:query_id, :user_id, :query_text, 'pending')
        """, {
            "query_id": query_id,
            "user_id": user_id,
            "query_text": data["query"]
        })
        
        # Initialize session state
        active_sessions[query_id] = SessionState(query_id)
        
        return {"query_id": query_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{query_id}")
async def get_query(query_id: str, request: Request):
    """Get query details"""
    user_id = await get_current_user(request)
    
    try:
        query = await database.fetch_one("""
            SELECT * FROM queries 
            WHERE query_id = :query_id AND user_id = :user_id
        """, {
            "query_id": query_id,
            "user_id": user_id
        })
        
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
            
        return dict(query)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{query_id}/refine")
async def start_refinement(
    query_id: str, 
    data: dict,
    request: Request,
    openrouter: OpenRouterClient = Depends(get_openrouter_client)
):
    """Start query refinement process"""
    user_id = await get_current_user(request)
    
    if query_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Query session not found")
        
    session = active_sessions[query_id]
    await session.update_stage(ProcessStage.REFINEMENT_STARTED)
    
    try:
        # Get current query
        query = await database.fetch_one("""
            SELECT query_text FROM queries
            WHERE query_id = :query_id AND user_id = :user_id
        """, {
            "query_id": query_id,
            "user_id": user_id
        })
        
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        current_query = query["query_text"]
        
        # Request refinement from LLM
        response = await openrouter.chat_completion(
            model="anthropic/claude-3-sonnet",
            messages=[{
                "role": "system",
                "content": "You are a research query refinement assistant. Help improve the clarity and specificity of research queries."
            }, {
                "role": "user", 
                "content": f"Please refine this research query: {current_query}"
            }]
        )
        
        refined_query = response["choices"][0]["message"]["content"]
        
        # Update database
        await database.execute("""
            UPDATE queries SET refined_query = :refined_query
            WHERE query_id = :query_id AND user_id = :user_id
        """, {
            "refined_query": refined_query,
            "query_id": query_id,
            "user_id": user_id
        })
        
        await session.update_stage(ProcessStage.REFINEMENT_COMPLETED)
        return {"refined_query": refined_query}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{query_id}/sources")
async def get_query_sources(query_id: str, request: Request):
    """Get sources for review"""
    user_id = await get_current_user(request)
    
    try:
        sources = await database.fetch_one("""
            SELECT web_sources, twitter_sources FROM queries
            WHERE query_id = :query_id AND user_id = :user_id
        """, {
            "query_id": query_id,
            "user_id": user_id
        })
        
        if not sources:
            raise HTTPException(status_code=404, detail="Query not found")
            
        return {
            "web_sources": sources["web_sources"],
            "twitter_sources": sources["twitter_sources"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{query_id}/sources/review")
async def submit_source_review(
    query_id: str,
    review: SourceReview,
    request: Request
):
    """Submit source review and reranking"""
    user_id = await get_current_user(request)
    
    if query_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Query session not found")
        
    session = active_sessions[query_id]
    
    try:
        # Get current sources
        sources = await database.fetch_one("""
            SELECT web_sources, twitter_sources FROM queries
            WHERE query_id = :query_id AND user_id = :user_id
        """, {
            "query_id": query_id,
            "user_id": user_id
        })
        
        if not sources:
            raise HTTPException(status_code=404, detail="Query not found")
            
        # Filter and rerank sources based on review
        web_sources = sources["web_sources"]
        twitter_sources = sources["twitter_sources"]
        
        # Filter out excluded sources
        filtered_web = [s for s in web_sources if s["url"] not in review.excluded]
        filtered_twitter = [s for s in twitter_sources if s["url"] not in review.excluded]
        
        # Rerank sources according to provided order
        reranked_sources = []
        for url in review.reranked_urls:
            source = next((s for s in filtered_web + filtered_twitter if s["url"] == url), None)
            if source:
                reranked_sources.append(source)
        
        # Update database with filtered and reranked sources
        await database.execute("""
            UPDATE queries 
            SET final_sources = :final_sources,
                web_sources = :web_sources,
                twitter_sources = :twitter_sources
            WHERE query_id = :query_id AND user_id = :user_id
        """, {
            "query_id": query_id,
            "user_id": user_id,
            "final_sources": json.dumps(reranked_sources),
            "web_sources": json.dumps(filtered_web),
            "twitter_sources": json.dumps(filtered_twitter)
        })
        
        await session.update_stage(ProcessStage.SOURCE_REVIEW_COMPLETED)
        return {"status": "success", "source_count": len(reranked_sources)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stream/{query_id}")
async def stream_progress(query_id: str, request: Request):
    """Stream progress updates for a query process using SSE"""
    if query_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Query session not found")
    
    async def event_generator():
        session = active_sessions[query_id]
        try:
            async for event in session.event_generator():
                if await request.is_disconnected():
                    break
                yield {
                    "event": "message",
                    "data": json.dumps(event)
                }
        except Exception as e:
            print(f"Error in event stream: {e}")
        finally:
            if session.is_completed:
                active_sessions.pop(query_id, None)
    
    return EventSourceResponse(event_generator())