"""
Draft Generator Module

This module handles the generation of draft content using approved sources.
It includes capabilities for initial draft creation and handling revisions
based on user feedback.
"""

import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from routers.openrouter import OpenRouterClient

# Using Claude 3 for high-quality writing
WRITER_MODEL = "openrouter/anthropic/claude-3-opus"

class Source(BaseModel):
    """Represents an approved source for writing"""
    id: str
    title: str
    content: str
    url: str
    metadata: Dict[str, Any]

class WritingRequest(BaseModel):
    """Input for draft generation"""
    query: str
    sources: List[Source]
    style_guide: Optional[Dict[str, Any]] = None
    previous_feedback: Optional[str] = None

async def generate_draft(request: WritingRequest) -> str:
    """Generate a draft based on approved sources"""
    client = OpenRouterClient()
    try:
        # Create the system prompt
        system_prompt = """You are an expert research writer tasked with creating a comprehensive 
        report based on provided sources. Follow these guidelines:
        1. Use factual information from sources
        2. Cite sources appropriately
        3. Maintain a clear, professional tone
        4. Organize content logically
        5. Highlight key findings and insights
        """
        
        if request.style_guide:
            system_prompt += f"\nAdditional style requirements:\n{request.style_guide}"
        
        # Format sources for the prompt
        sources_text = "\n\n".join([
            f"Source {i+1}: {s.title}\nURL: {s.url}\nContent: {s.content[:1000]}..."
            for i, s in enumerate(request.sources)
        ])
        
        user_prompt = f"""Query: {request.query}

Available Sources:
{sources_text}

{f'Previous feedback to address: {request.previous_feedback}' if request.previous_feedback else ''}

Write a comprehensive research report addressing the query using these sources."""

        # Generate the draft
        response = await client.chat_completion(
            model=WRITER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    finally:
        await client.client.aclose()

async def revise_draft(
    original_draft: str,
    feedback: str,
    sources: List[Source]
) -> str:
    """Revise a draft based on user feedback"""
    client = OpenRouterClient()
    try:
        system_prompt = """You are an expert editor tasked with revising a draft based on feedback.
        Maintain the draft's core content while addressing all feedback points thoroughly."""
        
        user_prompt = f"""Original Draft:
{original_draft}

User Feedback:
{feedback}

Available Sources:
""" + "\n\n".join([f"Source {i+1}: {s.title}\nURL: {s.url}" for i, s in enumerate(sources)])

        response = await client.chat_completion(
            model=WRITER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    finally:
        await client.client.aclose()