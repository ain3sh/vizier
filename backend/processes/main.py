"""Main module for coordinating writing flow

This module orchestrates the flow between Router_04, source agents, director and writer.
"""

import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel

from processes.connectors.router_04 import Router0_4, WritingContextRequest
from processes.sourcing.director import SourceDirector
from processes.sourcing.agent import SourceAgent
from processes.report.writer import Writer, WriterRequest

async def initialize_writing_pipeline(router_request: WritingContextRequest) -> Dict[str, Any]:
    """Initialize and connect all components of the writing pipeline"""
    
    # 1. Initialize Router_04 and get writing context
    router = Router0_4(
        router_request.cleaned_web_sources,
        router_request.cleaned_twitter_sources,
        router_request.user_context
    )
    writing_context = await router.prepare_writing_context()

    # 2. Initialize source agents through director
    director = SourceDirector()
    
    # Create and register source agents based on router assignments
    for agent_id, agent_info in writing_context.source_agents.items():
        # Get source URLs for this agent
        source_urls = [
            writing_context.reranked_sources[sid].metadata.url
            for sid in agent_info.assigned_sources
            if sid in writing_context.reranked_sources
        ]
        
        # Create agent with role-specific context
        agent = SourceAgent(
            meta_prompt=f"You are source agent {agent_id} specializing in themes: {agent_info.source_types}",
            source_urls=source_urls,
            role_context=f"Focus on sources of type: {agent_info.source_types}",
            objectives=[
                "Extract key insights relevant to query",
                "Identify connections between sources",
                "Prepare to answer clarification requests"
            ]
        )
        
        # Register with director
        await director.register_agent(
            agent_id,
            agent,
            agent_info.assigned_sources
        )

    # 3. Initialize writer with complete context
    writer = Writer()
    
    # 4. Create writer request with full context
    writer_request = WriterRequest(
        writing_context_id=writing_context.writing_context_id,
        refined_query=writing_context.refined_query,
        context_summary=writing_context.context_summary,
        source_agents=writing_context.source_agents,  
        reranked_sources=writing_context.reranked_sources,
        thematic_clusters=writing_context.thematic_clusters,
        report_style="technical",  # Can be parameterized
        user_background=router_request.user_context.get("user_background", {})
    )
    
    return {
        "writing_context": writing_context,
        "director": director,
        "writer": writer,
        "writer_request": writer_request
    }

async def execute_writing_pipeline(components: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the full writing pipeline with the initialized components"""
    
    writer = components["writer"]
    writer_request = components["writer_request"]
    
    # Generate initial draft
    response = await writer.generate_draft(writer_request)
    
    return {
        "draft_id": response.draft_id,
        "report_draft": response.report_draft,
        "suggested_improvements": response.suggested_improvements
    }

async def main():
    """Main entry point"""
    # Example usage
    router_request = WritingContextRequest(
        routing_id="example_routing",
        cleaned_web_sources={},  # Add sample sources
        cleaned_twitter_sources={},
        user_context={"user_background": {"user_type": "researcher"}}
    )
    
    try:
        # Initialize pipeline
        components = await initialize_writing_pipeline(router_request)
        
        # Execute pipeline
        result = await execute_writing_pipeline(components)
        
        print(f"Generated draft {result['draft_id']}")
        print(f"Suggested improvements: {result['suggested_improvements']}")
        
    except Exception as e:
        print(f"Error in writing pipeline: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())