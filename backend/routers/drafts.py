from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from database import database
from routers.queries import get_current_user, ProcessStage, active_sessions
from routers.openrouter import OpenRouterClient, get_openrouter_client
import asyncio
import json
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

router = APIRouter(prefix="/drafts", tags=["drafts"])

class DraftState:
    def __init__(self, draft_id: str):
        self.draft_id = draft_id
        self.content = ""
        self.is_completed = False
        self._event_queue = asyncio.Queue()
        
    async def update_content(self, new_content: str, is_final: bool = False):
        event = {
            "type": "content_update",
            "content": new_content,
            "timestamp": str(datetime.utcnow())
        }
        await self._event_queue.put(event)
        self.content = new_content
        
        if is_final:
            self.is_completed = True
            
    async def event_generator(self):
        while not self.is_completed or not self._event_queue.empty():
            try:
                event = await self._event_queue.get()
                yield event
            except Exception as e:
                print(f"Error in draft event generator: {e}")
                break

# Global draft states
active_drafts: Dict[str, DraftState] = {}

@router.post("/generate")
async def generate_draft(
    data: dict,
    request: Request, 
    openrouter: OpenRouterClient = Depends(get_openrouter_client)
):
    """Generate a new draft from query results"""
    user_id = await get_current_user(request)
    query_id = data.get("query_id")
    
    if not query_id:
        raise HTTPException(status_code=400, detail="query_id is required")
        
    try:
        # Get query and sources
        query = await database.fetch_one("""
            SELECT refined_query, sources FROM queries
            WHERE query_id = :query_id AND user_id = :user_id
        """, {
            "query_id": query_id,
            "user_id": user_id
        })
        
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        draft_id = str(uuid.uuid4())
        
        # Initialize draft state
        draft_state = DraftState(draft_id)
        active_drafts[draft_id] = draft_state
        
        # Update query session state
        if query_id in active_sessions:
            await active_sessions[query_id].update_stage(ProcessStage.WRITING_STARTED)
        
        # Create draft record
        await database.execute("""
            INSERT INTO drafts (draft_id, query_id, user_id, status)
            VALUES (:draft_id, :query_id, :user_id, 'writing')
        """, {
            "draft_id": draft_id,
            "query_id": query_id,
            "user_id": user_id
        })
        
        # Start async draft generation
        asyncio.create_task(generate_draft_content(
            draft_state,
            query["refined_query"],
            query["sources"],
            openrouter,
            query_id
        ))
        
        return {"draft_id": draft_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def generate_draft_content(
    draft_state: DraftState,
    refined_query: str,
    sources: list,
    openrouter: OpenRouterClient,
    query_id: str
):
    """Generate draft content using streaming completion"""
    try:
        messages = [{
            "role": "system",
            "content": "You are a research writing assistant. Create a well-structured draft based on the refined query and sources."
        }, {
            "role": "user",
            "content": f"Write a research draft answering this query: {refined_query}\n\nSources:\n{json.dumps(sources, indent=2)}"
        }]
        
        full_content = ""
        async for chunk in await openrouter.chat_completion(
            model="anthropic/claude-3-sonnet",
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=4000
        ):
            if chunk and chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                await draft_state.update_content(full_content)
                
        # Mark as complete
        await draft_state.update_content(full_content, is_final=True)
        
        # Update database
        await database.execute("""
            UPDATE drafts 
            SET content = :content, status = 'completed'
            WHERE draft_id = :draft_id
        """, {
            "content": full_content,
            "draft_id": draft_state.draft_id
        })
        
        # Update query session
        if query_id in active_sessions:
            await active_sessions[query_id].update_stage(ProcessStage.DRAFT_READY)
            
    except Exception as e:
        print(f"Error generating draft: {e}")
        if query_id in active_sessions:
            await active_sessions[query_id].update_stage(
                ProcessStage.DRAFT_READY,
                {"error": str(e)}
            )

@router.get("/{draft_id}")
async def get_draft(draft_id: str, request: Request):
    """Get draft details and content"""
    user_id = await get_current_user(request)
    
    try:
        draft = await database.fetch_one("""
            SELECT * FROM drafts
            WHERE draft_id = :draft_id AND user_id = :user_id
        """, {
            "draft_id": draft_id,
            "user_id": user_id
        })
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
            
        return dict(draft)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{draft_id}/accept")
async def accept_draft(draft_id: str, request: Request):
    """Accept and finalize a draft"""
    user_id = await get_current_user(request)
    
    try:
        # Get draft and associated query
        draft = await database.fetch_one("""
            SELECT query_id FROM drafts
            WHERE draft_id = :draft_id AND user_id = :user_id
        """, {
            "draft_id": draft_id,
            "user_id": user_id
        })
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
            
        # Update draft status    
        await database.execute("""
            UPDATE drafts SET status = 'accepted'
            WHERE draft_id = :draft_id
        """, {"draft_id": draft_id})
        
        # Update query session
        query_id = draft["query_id"]
        if query_id in active_sessions:
            await active_sessions[query_id].update_stage(ProcessStage.DRAFT_APPROVED)
            await active_sessions[query_id].update_stage(ProcessStage.COMPLETED)
            
        return {"status": "accepted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{draft_id}/reject")
async def reject_draft(draft_id: str, data: dict, request: Request):
    """Reject a draft with feedback"""
    user_id = await get_current_user(request)
    
    try:
        # Get draft
        draft = await database.fetch_one("""
            SELECT query_id FROM drafts
            WHERE draft_id = :draft_id AND user_id = :user_id
        """, {
            "draft_id": draft_id,
            "user_id": user_id
        })
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
            
        feedback = data.get("feedback", "")
            
        # Update draft status
        await database.execute("""
            UPDATE drafts 
            SET status = 'rejected', feedback = :feedback
            WHERE draft_id = :draft_id
        """, {
            "draft_id": draft_id,
            "feedback": feedback
        })
        
        return {"status": "rejected"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stream/{draft_id}")
async def stream_draft(draft_id: str, request: Request):
    """Stream draft content updates using SSE"""
    if draft_id not in active_drafts:
        raise HTTPException(status_code=404, detail="Draft generation not found")
        
    async def event_generator():
        draft_state = active_drafts[draft_id]
        try:
            async for event in draft_state.event_generator():
                if await request.is_disconnected():
                    break
                yield {
                    "event": "message",
                    "data": json.dumps(event)
                }
        except Exception as e:
            print(f"Error in draft stream: {e}")
        finally:
            if draft_state.is_completed:
                active_drafts.pop(draft_id, None)
    
    return EventSourceResponse(event_generator())
