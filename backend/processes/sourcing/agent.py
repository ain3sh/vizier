"""
Source Agent implementation for Vizier.

This module implements an autonomous agent capable of deep source analysis,
insight extraction, and maintaining context for writer clarifications.
"""

import json 
import asyncio
from typing import Dict, List, Optional, Union, Any, Literal, Set
from dataclasses import dataclass
from bs4 import BeautifulSoup
import httpx
import PyPDF2
import io
import trafilatura
import tiktoken
from urllib.parse import urlparse
from pydantic import BaseModel, Field
from datetime import datetime
from routers.openrouter import OpenRouterClient

DEFAULT_MODEL = "openrouter/anthropic/claude-3-opus"
TOKENS_PER_CHUNK = 2048
MAX_CHUNKS = 20  # Maximum number of chunks we'll process at once
SUMMARY_MAX_TOKENS = 4000
MAX_TOKENS = 100000
EXPLORATION_TEMPERATURE = 0.3
CLARIFICATION_TEMPERATURE = 0.7

class ProcessedQuote(BaseModel):
    """A quote extracted from source content"""
    content: str = Field(description="The quoted text")
    context: str = Field(description="Context around the quote")
    relevance: float = Field(description="Relevance score (0-1)")
    themes: List[str] = Field(description="Themes this quote relates to")

class SourceInsight(BaseModel):
    """An insight extracted from source analysis"""
    content: str = Field(description="The insight content")
    confidence: float = Field(description="Confidence score (0-1)")
    related_insights: List[str] = Field(description="Related insights to explore")
    supporting_quotes: List[str] = Field(description="Supporting quotes")
    themes: List[str] = Field(description="Themes this insight relates to")

class ProcessedSource(BaseModel):
    """A fully processed source with extracted insights"""
    source_id: str = Field(description="Unique identifier for the source")
    source_type: str = Field(description="Type of source (web, academic, etc)")
    confidence_score: float = Field(description="Overall confidence in analysis (0-1)")
    complexity_score: float = Field(description="Technical complexity score (0-1)")
    domain_tags: List[str] = Field(description="Domain-specific tags")
    timestamp: str = Field(description="Processing timestamp")
    potential_clarifications: List[str] = Field(description="Potential areas for clarification")
    key_insights: List[SourceInsight] = Field(description="Key insights extracted")
    major_themes: List[str] = Field(description="Major themes identified")
    quoted_content: Dict[str, ProcessedQuote] = Field(description="Extracted quotes")
    summary: str = Field(description="Brief summary of the source")

class ExplorationPlan(BaseModel):
    """Plan for exploring a source's content"""
    content_type: str = Field(description="Type of content being analyzed")
    key_areas: List[str] = Field(description="Key areas to explore")
    exploration_steps: List[Dict[str, Any]] = Field(description="Planned exploration steps")
    priority_themes: List[str] = Field(description="Themes to prioritize")

class SourceAgent:
    """An autonomous agent for deep source analysis and insight extraction"""
    
    def __init__(
        self,
        meta_prompt: str,
        source_urls: List[str],
        role_context: str,
        objectives: List[str],
        model: str = DEFAULT_MODEL
    ):
        """
        Initialize a source agent.
        
        Args:
            meta_prompt: High-level guidance for the agent
            source_urls: List of source URLs to process
            role_context: Context about the agent's role
            objectives: List of analysis objectives
            model: LLM model to use
        """
        self.client = OpenRouterClient()
        self.model = model
        self.meta_prompt = meta_prompt
        self.source_urls = source_urls
        self.role_context = role_context
        self.objectives = objectives
        
        # Internal state
        self.processed_sources: Dict[str, ProcessedSource] = {}
        self.exploration_history: List[Dict[str, Any]] = []
        self.clarification_cache: Dict[str, Dict[str, Any]] = {}
        self.theme_expertise: Set[str] = set()
        self.confidence_thresholds: Dict[str, float] = {
            "insight": 0.7,
            "quote": 0.8,
            "clarification": 0.75
        }

    async def _plan_exploration(self, content: str) -> ExplorationPlan:
        """Create a plan for exploring source content"""
        prompt = f"""
        Create an exploration plan for analyzing this content.

        Content Type: Auto-detect from content
        Content Preview: {content[:1000]}...

        Role Context: {self.role_context}
        Objectives: {json.dumps(self.objectives)}

        Return a JSON exploration plan including:
        1. Content type classification
        2. Key areas to explore
        3. Specific exploration steps
        4. Priority themes to focus on
        """

        try:
            response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=EXPLORATION_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            plan_dict = json.loads(response["choices"][0]["message"]["content"])
            return ExplorationPlan(**plan_dict)
            
        except Exception as e:
            print(f"Error creating exploration plan: {e}")
            return ExplorationPlan(
                content_type="unknown",
                key_areas=[],
                exploration_steps=[],
                priority_themes=[]
            )

    async def _extract_quotes(self, content: str, themes: List[str]) -> Dict[str, ProcessedQuote]:
        """Extract relevant quotes from content"""
        prompt = f"""
        Extract key quotes from the content that support our analysis objectives.
        For each quote:
        1. Include surrounding context
        2. Rate relevance (0-1)
        3. Tag with relevant themes
        4. Only include quotes with relevance > {self.confidence_thresholds['quote']}

        Content: {content}
        Themes to Consider: {themes}
        """

        try:
            response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MAX_TOKENS,
                temperature=EXPLORATION_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            quotes_dict = json.loads(response["choices"][0]["message"]["content"])
            return {
                qid: ProcessedQuote(**quote_data)
                for qid, quote_data in quotes_dict.items()
            }
            
        except Exception as e:
            print(f"Error extracting quotes: {e}")
            return {}

    async def _identify_insights(
        self,
        content: str,
        quotes: Dict[str, ProcessedQuote]
    ) -> List[SourceInsight]:
        """Identify key insights from content and quotes"""
        prompt = f"""
        Based on the content and extracted quotes, identify key insights that:
        1. Address our analysis objectives
        2. Have confidence > {self.confidence_thresholds['insight']}
        3. Are supported by specific quotes
        4. Connect to broader themes
        5. Suggest related areas to explore

        Content: {content}
        Extracted Quotes: {json.dumps(quotes)}
        Objectives: {json.dumps(self.objectives)}
        """

        try:
            response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MAX_TOKENS,
                temperature=EXPLORATION_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            insights_list = json.loads(response["choices"][0]["message"]["content"])
            return [SourceInsight(**insight_data) for insight_data in insights_list]
            
        except Exception as e:
            print(f"Error identifying insights: {e}")
            return []

    async def process_source(self, source_id: str, url: str) -> ProcessedSource:
        """Process a single source through the full pipeline with deep exploration"""
        try:
            # Extract content (placeholder - implement actual extraction)
            content = await self.extract_source_content(url)
            if not content:
                raise ValueError(f"Could not extract content from {url}")
                
            # Create exploration plan
            plan = await self._plan_exploration(content)
            
            # Extract quotes
            quotes = await self._extract_quotes(content, plan.priority_themes)
            
            # Identify insights
            insights = await self._identify_insights(content, quotes)
            
            # Calculate aggregate metrics
            avg_confidence = sum(i.confidence for i in insights) / len(insights) if insights else 0
            
            # Update theme expertise
            self.theme_expertise.update(plan.priority_themes)
            
            # Generate summary based on insights
            summary_prompt = f"""
            Create a brief summary of this source based on the extracted insights.
            Focus on key findings relevant to our objectives.

            Insights: {json.dumps([i.dict() for i in insights])}
            """
            
            summary_response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            summary = summary_response["choices"][0]["message"]["content"]
            
            # Create processed source
            processed = ProcessedSource(
                source_id=source_id,
                source_type=plan.content_type,
                confidence_score=avg_confidence,
                complexity_score=0.7,  # TODO: Implement complexity scoring
                domain_tags=plan.key_areas,
                timestamp=datetime.now().isoformat(),
                potential_clarifications=[c for i in insights for c in i.related_insights],
                key_insights=insights,
                major_themes=plan.priority_themes,
                quoted_content=quotes,
                summary=summary
            )
            
            self.processed_sources[source_id] = processed
            return processed
            
        except Exception as e:
            print(f"Error processing source {url}: {e}")
            raise

    async def process_all_sources(self) -> Dict[str, ProcessedSource]:
        """Process all assigned sources"""
        results = {}
        for i, url in enumerate(self.source_urls):
            source_id = f"source_{i}"
            try:
                processed = await self.process_source(source_id, url)
                results[source_id] = processed
            except Exception as e:
                print(f"Error processing source {url}: {e}")
                continue
        return results

    async def get_clarification(self, query: str, source_id: str) -> str:
        """
        Respond to a clarification request about a specific source with 
        thorough exploration and verification of the response.
        """
        if source_id not in self.processed_sources:
            return f"Source {source_id} not found"
            
        # Check cache first
        cache_key = f"{source_id}:{query}"
        if cache_key in self.clarification_cache:
            return self.clarification_cache[cache_key]["response"]
            
        source = self.processed_sources[source_id]
        
        # Find relevant insights and quotes
        relevant_insights = [
            i for i in source.key_insights
            if any(theme in query.lower() for theme in i.themes)
        ]
        
        relevant_quotes = [
            quote for quote in source.quoted_content.values()
            if any(theme in query.lower() for theme in quote.themes)
        ]
        
        clarification_prompt = f"""
        Answer this clarification request about source {source_id}:
        
        Query: {query}
        
        Source Summary: {source.summary}
        
        Relevant Insights: 
        {json.dumps([i.dict() for i in relevant_insights], indent=2)}
        
        Supporting Quotes:
        {json.dumps([q.dict() for q in relevant_quotes], indent=2)}
        
        Requirements:
        1. Answer specifically based on source content
        2. Support claims with quotes where possible
        3. Note if information is uncertain or needs additional context
        4. Only include high-confidence information
        5. Suggest related areas to explore if relevant
        """
        
        try:
            # Generate initial response
            response = await self.client.chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.meta_prompt},
                    {"role": "user", "content": clarification_prompt}
                ],
                max_tokens=1000,
                temperature=CLARIFICATION_TEMPERATURE
            )
            
            clarification = response["choices"][0]["message"]["content"]
            
            # Verify response quality
            verification_prompt = f"""
            Verify this clarification response:
            
            Original Query: {query}
            Response: {clarification}
            
            Check:
            1. Does it directly answer the query?
            2. Is it supported by source content?
            3. Is confidence properly qualified?
            4. Are important caveats noted?
            
            Return a confidence score (0-1) and any issues found.
            """
            
            verify_response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": verification_prompt}],
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            verification = json.loads(verify_response["choices"][0]["message"]["content"])
            confidence = verification.get("confidence", 0)
            
            # Only cache if confidence meets threshold
            if confidence >= self.confidence_thresholds["clarification"]:
                self.clarification_cache[cache_key] = {
                    "response": clarification,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat()
                }
            
            return clarification
            
        except Exception as e:
            print(f"Error generating clarification: {e}")
            return f"Error clarifying source {source_id}: {str(e)}"

    async def extract_source_content(self, url: str) -> Optional[str]:
        """Extract content from a source URL"""
        # TODO: Implement actual content extraction
        # This is a placeholder that should be replaced with real extraction logic
        return f"Sample content from {url}"