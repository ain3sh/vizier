"""
Source Director Module

Coordinates multiple source agents and manages their interactions with the writer.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pydantic import BaseModel, Field

from .agent import SourceAgent, ProcessedSource
from ..connectors.router_04 import WritingContextResponse

class DirectorRequest(BaseModel):
    """Request to the director for source agent coordination"""
    agent_id: str = Field(description="ID of the source agent to query")
    source_id: str = Field(description="ID of the source to get clarification about")
    query: str = Field(description="The clarification query")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")

class DirectorResponse(BaseModel):
    """Response from the director containing source agent results"""
    agent_id: str = Field(description="ID of the responding source agent")
    source_id: str = Field(description="ID of the source that was clarified")
    clarification: str = Field(description="The clarification response")
    confidence: float = Field(description="Confidence score for the response (0-1)")
    supporting_quotes: List[str] = Field(description="Supporting quotes from the source")

class AgentState(BaseModel):
    """Track the state and performance of a source agent"""
    agent_id: str = Field(description="Unique identifier for the agent")
    assigned_sources: List[str] = Field(description="Sources assigned to this agent")
    active_queries: int = Field(default=0, description="Number of active queries")
    completed_queries: int = Field(default=0, description="Number of completed queries")
    avg_response_time: float = Field(default=0.0, description="Average response time in seconds")
    last_active: datetime = Field(default_factory=datetime.now, description="Last activity timestamp")

class SourceDirector:
    """
    Coordinates source agents and manages their interactions with the writer.
    
    Key responsibilities:
    1. Track source agent states and capabilities
    2. Route queries to appropriate agents
    3. Handle parallel processing of multiple queries
    4. Manage agent load balancing
    5. Monitor agent performance
    6. Handle failover if needed
    """
    
    def __init__(self):
        self.agents: Dict[str, SourceAgent] = {}
        self.agent_states: Dict[str, AgentState] = {}
        self.source_assignments: Dict[str, str] = {}  # source_id -> agent_id
        self.query_history: List[Dict[str, Any]] = []
        self.max_parallel_queries = 5
        self.query_semaphore = asyncio.Semaphore(self.max_parallel_queries)

    async def register_agent(
        self, 
        agent_id: str, 
        agent: SourceAgent, 
        assigned_sources: List[str]
    ) -> None:
        """Register a new source agent with the director"""
        self.agents[agent_id] = agent
        self.agent_states[agent_id] = AgentState(
            agent_id=agent_id,
            assigned_sources=assigned_sources
        )
        
        # Update source assignments
        for source_id in assigned_sources:
            self.source_assignments[source_id] = agent_id

    def _get_agent_for_source(self, source_id: str) -> Optional[str]:
        """Get the agent ID responsible for a source"""
        return self.source_assignments.get(source_id)

    def _update_agent_metrics(
        self, 
        agent_id: str, 
        response_time: float, 
        success: bool
    ) -> None:
        """Update performance metrics for an agent"""
        if agent_id in self.agent_states:
            state = self.agent_states[agent_id]
            state.completed_queries += 1
            
            # Update average response time with exponential moving average
            alpha = 0.1  # Smoothing factor
            state.avg_response_time = (
                (1 - alpha) * state.avg_response_time + 
                alpha * response_time
            )
            
            state.last_active = datetime.now()

    async def _process_query(
        self, 
        agent: SourceAgent,
        agent_id: str,
        source_id: str,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DirectorResponse:
        """Process a single query through a source agent"""
        start_time = datetime.now()
        
        try:
            # Get clarification from the agent
            clarification = await agent.get_clarification(query, source_id)
            
            # Get supporting quotes if available
            source = agent.processed_sources.get(source_id)
            quotes = list(source.quoted_content.values()) if source else []
            
            # Calculate confidence based on agent's source analysis
            confidence = source.confidence_score if source else 0.5
            
            response = DirectorResponse(
                agent_id=agent_id,
                source_id=source_id,
                clarification=clarification,
                confidence=confidence,
                supporting_quotes=quotes[:3]  # Limit to top 3 quotes
            )
            
        except Exception as e:
            print(f"Error processing query through agent {agent_id}: {e}")
            response = DirectorResponse(
                agent_id=agent_id,
                source_id=source_id,
                clarification=f"Error: {str(e)}",
                confidence=0.0,
                supporting_quotes=[]
            )
            
        # Update metrics
        response_time = (datetime.now() - start_time).total_seconds()
        self._update_agent_metrics(
            agent_id,
            response_time,
            response.confidence > 0
        )
        
        return response

    async def get_clarification(self, request: DirectorRequest) -> Optional[DirectorResponse]:
        """
        Get clarification about a source from the responsible agent.
        
        Args:
            request: The clarification request
            
        Returns:
            DirectorResponse with the clarification if successful
        """
        # Validate request
        agent_id = request.agent_id
        if agent_id not in self.agents:
            print(f"Unknown agent ID: {agent_id}")
            return None
            
        source_id = request.source_id
        assigned_agent = self._get_agent_for_source(source_id)
        if assigned_agent != agent_id:
            print(f"Source {source_id} not assigned to agent {agent_id}")
            return None
            
        # Get the agent
        agent = self.agents[agent_id]
        
        # Process with concurrency control
        async with self.query_semaphore:
            try:
                # Update active queries count
                self.agent_states[agent_id].active_queries += 1
                
                # Process the query
                response = await self._process_query(
                    agent,
                    agent_id,
                    source_id,
                    request.query,
                    request.context
                )
                
                # Log the query
                self.query_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "agent_id": agent_id,
                    "source_id": source_id,
                    "query": request.query,
                    "context": request.context,
                    "success": response.confidence > 0
                })
                
                return response
                
            finally:
                # Update active queries count
                self.agent_states[agent_id].active_queries -= 1

    async def process_parallel_queries(
        self, 
        requests: List[DirectorRequest]
    ) -> List[Optional[DirectorResponse]]:
        """
        Process multiple queries in parallel while respecting concurrency limits.
        
        Args:
            requests: List of clarification requests
            
        Returns:
            List of responses (None for failed requests)
        """
        async def process_single(request: DirectorRequest) -> Optional[DirectorResponse]:
            return await self.get_clarification(request)
            
        # Process all requests in parallel
        responses = await asyncio.gather(
            *[process_single(req) for req in requests],
            return_exceptions=True
        )
        
        # Filter out exceptions
        return [
            r if not isinstance(r, Exception) else None
            for r in responses
        ]

    def get_agent_status(self, agent_id: str) -> Optional[AgentState]:
        """Get the current state of a source agent"""
        return self.agent_states.get(agent_id)

    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get performance metrics for a source agent"""
        state = self.agent_states.get(agent_id)
        if not state:
            return {}
            
        return {
            "completed_queries": state.completed_queries,
            "avg_response_time": state.avg_response_time,
            "current_load": state.active_queries
        }

    async def check_agent_health(self) -> Dict[str, bool]:
        """Check the health status of all agents"""
        results = {}
        for agent_id, state in self.agent_states.items():
            # Consider an agent unhealthy if:
            # 1. It has been inactive for too long
            # 2. Its average response time is too high
            # 3. It has too many active queries
            
            inactive_time = (datetime.now() - state.last_active).total_seconds()
            is_healthy = (
                inactive_time < 3600 and  # Less than 1 hour inactive
                state.avg_response_time < 30 and  # Average response under 30s
                state.active_queries < self.max_parallel_queries  # Not overloaded
            )
            results[agent_id] = is_healthy
            
        return results