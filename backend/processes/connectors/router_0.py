"""
Router Planning Flow Module

This module implements the core routing functionality for Vizier's research planning process.
It contains the Router0 agent-centric router that creates rich search contexts for external 
retrieval agents. Instead of hardcoded rules, it focuses on generating guidance that helps agents 
understand the search intent, quality requirements, and context necessary for high-quality 
research.

Router0 is the first step in the research workflow after query refinement, responsible for
creating specialized search contexts for different agent types before data collection begins.
"""

import os, asyncio, json
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from routers.openrouter import OpenRouterClient

# constants
ROUTER_MODEL = "openrouter/mistralai/mixtral-8x7b-instruct" # can use a smaller model for routing


class SourceType(str, Enum):
    """Types of external data sources"""
    WEB = "web"
    TWITTER = "twitter"
    ACADEMIC = "academic"
    NEWS = "news"
    BLOG = "blog"
    FORUM = "forum"
    OTHER = "other"

class SourceRelevance(str, Enum):
    """Relevance categories for sources"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    IRRELEVANT = "irrelevant"


class UserBackground(BaseModel):
    """User background information for context routing"""
    user_type: str = Field(description="Type of user (e.g., 'Specialized Professional')")
    research_purpose: str = Field(description="What the user will use Vizier for")
    user_description: str = Field(description="Brief description of who the user is")
    query_frequency: str = Field(description="How often the query will be run (daily/weekly/monthly)")


class SourceExplorationGuidance(BaseModel):
    """Agent-centric guidance for source exploration"""
    overall_strategy: str = Field(description="High-level search strategy guidance")
    source_priorities: Dict[str, float] = Field(description="Relative importance of different source types")
    quality_indicators: Dict[str, List[str]] = Field(description="What indicates quality for each source type")
    depth_guidance: str = Field(description="Guidance on technical depth")
    recency_guidance: str = Field(description="Guidance on source recency")
    authority_guidance: str = Field(description="How to evaluate source authority")
    special_considerations: Optional[str] = Field(None, description="Special research considerations")


class RoutingRequest(BaseModel):
    """Request model for routing a refined query"""
    refined_query: str = Field(description="The refined query to route")
    background: UserBackground = Field(description="User background information")
    domain_context: Optional[Dict[str, Any]] = Field(None, description="Additional domain context")
    exploration_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences for exploration")

class RoutingResponse(BaseModel):
    """Response model for routing results"""
    routing_id: str = Field(description="Unique identifier for this routing operation")
    search_guidance: SourceExplorationGuidance = Field(description="Agent-centric search guidance")
    web_agent_context: Dict[str, Any] = Field(description="Context for web search agents")
    twitter_agent_context: Dict[str, Any] = Field(description="Context for Twitter search agents")
    academic_agent_context: Optional[Dict[str, Any]] = Field(None, description="Context for academic search agents")


class Router0:
    """
    Agent-centric router that provides strategic guidance for external data collection agents.
    
    Instead of hardcoded rules and keyword extraction, Router0 uses LLM capabilities to:
    1. Understand the query intent and user needs
    2. Generate rich guidance for downstream search agents
    3. Create specialized contexts for different agent types
    """

    def __init__(self, model: str = ROUTER_MODEL):
        """Initialize the Router0 instance with an LLM client"""
        self.client = OpenRouterClient()
        self.model = model

    def _generate_routing_id(self) -> str:
        """Generate a unique identifier for the routing operation"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = os.urandom(4).hex()
        return f"route_{timestamp}_{random_part}"
    
    async def _generate_search_guidance(self, query: str, background: UserBackground, 
                                      domain_context: Optional[Dict[str, Any]] = None) -> SourceExplorationGuidance:
        """
        Use LLM to generate search guidance for external agents.
        
        Args:
            query: The refined query
            background: User background information
            domain_context: Optional additional domain context
            
        Returns:
            SourceExplorationGuidance with agent-centric search recommendations
        """
        # Create the prompt for search guidance
        prompt = f"""
        You are an expert research strategist helping plan a search strategy for a complex query.

        # QUERY DETAILS
        Refined Query: {query}

        # USER CONTEXT
        User Type: {background.user_type}
        Research Purpose: {background.research_purpose}
        User Description: {background.user_description}
        Query Frequency: {background.query_frequency}

        # TASK
        Create a detailed search strategy that will help guide intelligent search agents to find the most valuable sources for this query.
        
        Provide guidance on:
        1. Overall search strategy (key objectives, approach)
        2. Source type priorities (assign a value from 0.0-1.0 to each of: WEB, TWITTER, ACADEMIC, NEWS, BLOG, FORUM)
        3. Quality indicators for each source type
        4. Technical depth requirements
        5. Recency considerations
        6. Authority evaluation criteria
        7. Any special considerations for this specific query

        # OUTPUT FORMAT
        Provide a JSON object with the following structure:
        ```json
        {{
            "overall_strategy": "Clear strategic guidance for search agents",
            "source_priorities": {{
                "WEB": 0.9,
                "TWITTER": 0.7,
                "ACADEMIC": 0.8,
                "NEWS": 0.6,
                "BLOG": 0.5,
                "FORUM": 0.4
            }},
            "quality_indicators": {{
                "WEB": ["indicator1", "indicator2", "indicator3"],
                "TWITTER": ["indicator1", "indicator2", "indicator3"],
                "ACADEMIC": ["indicator1", "indicator2", "indicator3"]
            }},
            "depth_guidance": "Guidance on required technical depth",
            "recency_guidance": "Guidance on source recency",
            "authority_guidance": "How to evaluate source authority",
            "special_considerations": "Any special recommendations for this query"
        }}
        ```

        Focus on providing actionable, specific guidance that helps agents make intelligent decisions about source quality and relevance.
        """
        
        # If we have domain context, add it to the prompt
        if domain_context:
            domain_context_str = json.dumps(domain_context, indent=2)
            prompt += f"\n\n# DOMAIN CONTEXT\n{domain_context_str}"
        
        # Call the LLM to generate the search guidance
        try:
            response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,  # Low temperature for more consistent results
                max_tokens=1500,
            )
            
            # Extract the JSON response
            guidance_json = json.loads(response["choices"][0]["message"]["content"])
            
            # Create and return the SourceExplorationGuidance object
            return SourceExplorationGuidance(
                overall_strategy=guidance_json["overall_strategy"],
                source_priorities=guidance_json["source_priorities"],
                quality_indicators=guidance_json["quality_indicators"],
                depth_guidance=guidance_json["depth_guidance"],
                recency_guidance=guidance_json["recency_guidance"],
                authority_guidance=guidance_json["authority_guidance"],
                special_considerations=guidance_json.get("special_considerations")
            )
            
        except Exception as e:
            # Fallback values if the LLM call fails
            print(f"Error generating search guidance: {e}")
            return SourceExplorationGuidance(
                overall_strategy=f"Find high-quality, relevant sources for: {query}",
                source_priorities={"WEB": 0.9, "TWITTER": 0.7, "ACADEMIC": 0.8, 
                                  "NEWS": 0.6, "BLOG": 0.5, "FORUM": 0.4},
                quality_indicators={
                    "WEB": ["Authoritative source", "Comprehensive coverage", "Technical accuracy"],
                    "TWITTER": ["Expert authors", "Substantive threads", "Evidence-backed claims"],
                    "ACADEMIC": ["Peer-reviewed", "Cited by experts", "Rigorous methodology"]
                },
                depth_guidance="Match technical depth to user background and query complexity",
                recency_guidance="Prioritize recent sources unless seeking foundational knowledge",
                authority_guidance="Seek sources from recognized experts and institutions",
                special_considerations=None
            )
    
    async def _generate_web_search_context(self, query: str, background: UserBackground, 
                                        guidance: SourceExplorationGuidance) -> Dict[str, Any]:
        """
        Generate a context object for web search agents.
        
        Args:
            query: The refined query
            background: User background information
            guidance: Generated search guidance
            
        Returns:
            Context dictionary for web search agents
        """
        # Create the prompt for web search context
        prompt = f"""
        You are an expert search strategist creating a search plan for web sources.
        
        # QUERY
        {query}
        
        # USER CONTEXT
        User Type: {background.user_type}
        Research Purpose: {background.research_purpose}
        
        # SEARCH GUIDANCE
        Overall Strategy: {guidance.overall_strategy}
        Web Source Priority: {guidance.source_priorities.get("WEB", 0.8)}/1.0
        Depth Guidance: {guidance.depth_guidance}
        Recency Guidance: {guidance.recency_guidance}
        Authority Guidance: {guidance.authority_guidance}
        
        Web Quality Indicators:
        {json.dumps(guidance.quality_indicators.get("WEB", []), indent=2)}
        
        # TASK
        Create a web search context object that will guide a web search agent. Include:
        1. Search parameters (timeframe, filters, etc.)
        2. Priority topics/aspects to investigate
        3. Specific domains or source types to prioritize
        4. Guidelines for evaluating source quality
        5. Any specific search strategies that would be effective
        
        # OUTPUT FORMAT
        Provide ONLY a JSON object with search parameters and guidance:
        ```json
        {{
            "search_parameters": {{
                "timeframe": "...",
                "filters": [...],
                "excluded_domains": [...],
                "preferred_domains": [...]
            }},
            "priority_topics": [...],
            "depth_requirements": "...",
            "quality_evaluation": [...],
            "search_strategies": [...]
        }}
        ```
        """
        
        # Call the LLM to generate the web search context
        try:
            response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1200,
            )
            
            # Extract and return the JSON response
            web_context = json.loads(response["choices"][0]["message"]["content"])
            return web_context
            
        except Exception as e:
            # Fallback values if the LLM call fails
            print(f"Error generating web search context: {e}")
            return {
                "search_parameters": {
                    "timeframe": "past year",
                    "filters": [],
                    "excluded_domains": [],
                    "preferred_domains": []
                },
                "priority_topics": [query],
                "depth_requirements": guidance.depth_guidance,
                "quality_evaluation": guidance.quality_indicators.get("WEB", []),
                "search_strategies": ["Use exact phrases from the query"]
            }
    
    async def _generate_twitter_search_context(self, query: str, background: UserBackground, 
                                           guidance: SourceExplorationGuidance) -> Dict[str, Any]:
        """
        Generate a context object for Twitter search agents.
        
        Args:
            query: The refined query
            background: User background information
            guidance: Generated search guidance
            
        Returns:
            Context dictionary for Twitter search agents
        """
        # Create the prompt for Twitter search context
        prompt = f"""
        You are an expert social media search strategist creating a search plan for Twitter.
        
        # QUERY
        {query}
        
        # USER CONTEXT
        User Type: {background.user_type}
        Research Purpose: {background.research_purpose}
        
        # SEARCH GUIDANCE
        Overall Strategy: {guidance.overall_strategy}
        Twitter Source Priority: {guidance.source_priorities.get("TWITTER", 0.7)}/1.0
        Depth Guidance: {guidance.depth_guidance}
        Recency Guidance: {guidance.recency_guidance}
        Authority Guidance: {guidance.authority_guidance}
        
        Twitter Quality Indicators:
        {json.dumps(guidance.quality_indicators.get("TWITTER", []), indent=2)}
        
        # TASK
        Create a Twitter search context object that will guide a Twitter search agent. Include:
        1. Search parameters (timeframe, engagement thresholds, etc.)
        2. Account types to prioritize 
        3. Relevant hashtags for the query
        4. Guidelines for evaluating tweet and thread quality
        5. Any specific Twitter search strategies that would be effective
        
        # OUTPUT FORMAT
        Provide ONLY a JSON object with search parameters and guidance:
        ```json
        {{
            "search_parameters": {{
                "timeframe": "...",
                "min_engagement": ...,
                "verified_only": true/false,
                "exclude_terms": [...]
            }},
            "priority_accounts": [...],
            "relevant_hashtags": [...],
            "quality_evaluation": [...],
            "search_strategies": [...]
        }}
        ```
        """
        
        # Call the LLM to generate the Twitter search context
        try:
            response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1200,
            )
            
            # Extract and return the JSON response
            twitter_context = json.loads(response["choices"][0]["message"]["content"])
            return twitter_context
            
        except Exception as e:
            # Fallback values if the LLM call fails
            print(f"Error generating Twitter search context: {e}")
            return {
                "search_parameters": {
                    "timeframe": "past week",
                    "min_engagement": 5,
                    "verified_only": False,
                    "exclude_terms": ["spam", "giveaway", "promotion"]
                },
                "priority_accounts": [],
                "relevant_hashtags": [],
                "quality_evaluation": guidance.quality_indicators.get("TWITTER", []),
                "search_strategies": ["Use key terms from query"]
            }
    
    async def _generate_academic_search_context(self, query: str, background: UserBackground, 
                                            guidance: SourceExplorationGuidance) -> Optional[Dict[str, Any]]:
        """
        Generate a context object for academic search agents if needed.
        
        Args:
            query: The refined query
            background: User background information
            guidance: Generated search guidance
            
        Returns:
            Context dictionary for academic search agents, or None if not needed
        """
        # Check if academic sources are important for this query
        academic_priority = guidance.source_priorities.get("ACADEMIC", 0.0)
        if academic_priority < 0.5:
            return None
            
        # Create the prompt for academic search context
        prompt = f"""
        You are an expert academic research strategist creating a search plan for scholarly sources.
        
        # QUERY
        {query}
        
        # USER CONTEXT
        User Type: {background.user_type}
        Research Purpose: {background.research_purpose}
        
        # SEARCH GUIDANCE
        Overall Strategy: {guidance.overall_strategy}
        Academic Source Priority: {academic_priority}/1.0
        Depth Guidance: {guidance.depth_guidance}
        Recency Guidance: {guidance.recency_guidance}
        Authority Guidance: {guidance.authority_guidance}
        
        Academic Quality Indicators:
        {json.dumps(guidance.quality_indicators.get("ACADEMIC", []), indent=2)}
        
        # TASK
        Create an academic search context object that will guide a scholarly search agent. Include:
        1. Search parameters (publication date range, citation thresholds, etc.)
        2. Key journals or conferences to prioritize
        3. Relevant academic fields/disciplines
        4. Guidelines for evaluating paper quality and relevance
        5. Any specific academic search strategies that would be effective
        
        # OUTPUT FORMAT
        Provide ONLY a JSON object with search parameters and guidance:
        ```json
        {{
            "search_parameters": {{
                "date_range": "...",
                "min_citations": ...,
                "open_access_preferred": true/false,
                "include_preprints": true/false
            }},
            "priority_venues": [...],
            "relevant_fields": [...],
            "quality_evaluation": [...],
            "search_strategies": [...]
        }}
        ```
        """
        
        # Call the LLM to generate the academic search context
        try:
            response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1200,
            )
            
            # Extract and return the JSON response
            academic_context = json.loads(response["choices"][0]["message"]["content"])
            return academic_context
            
        except Exception as e:
            # Fallback values if the LLM call fails
            print(f"Error generating academic search context: {e}")
            return {
                "search_parameters": {
                    "date_range": "past 3 years",
                    "min_citations": 0,
                    "open_access_preferred": True,
                    "include_preprints": True
                },
                "priority_venues": [],
                "relevant_fields": [],
                "quality_evaluation": guidance.quality_indicators.get("ACADEMIC", []),
                "search_strategies": ["Use technical terms from query"]
            }
    
    async def route_query(self, request: RoutingRequest) -> RoutingResponse:
        """
        Route a refined query by providing strategic guidance for external retrieval agents.

        Args:
            request: The routing request containing query and user background
    
        Returns:
            Routing response with exploration strategies and context
        """
        # Generate a unique routing ID
        routing_id = self._generate_routing_id()
        
        # Generate search guidance (agent-centric, not hardcoded rules)
        search_guidance = await self._generate_search_guidance(
            request.refined_query,
            request.background,
            request.domain_context
        )
        
        # Generate contexts for different agent types in parallel
        web_context_task = self._generate_web_search_context(
            request.refined_query,
            request.background,
            search_guidance
        )
        
        twitter_context_task = self._generate_twitter_search_context(
            request.refined_query,
            request.background,
            search_guidance
        )
        
        academic_context_task = self._generate_academic_search_context(
            request.refined_query,
            request.background,
            search_guidance
        )
        
        # Wait for all context generation tasks to complete
        web_context, twitter_context, academic_context = await asyncio.gather(
            web_context_task,
            twitter_context_task,
            academic_context_task
        )
        
        # Create and return the routing response
        return RoutingResponse(
            routing_id=routing_id,
            search_guidance=search_guidance,
            web_agent_context=web_context,
            twitter_agent_context=twitter_context,
            academic_agent_context=academic_context
        )


async def route_query(request: RoutingRequest) -> RoutingResponse:
    """
    API endpoint for routing a refined query to data sources.
    
    Args:
        request: The routing request
        
    Returns:
        RoutingResponse with exploration strategies and context
    """
    router = Router0()
    response = await router.route_query(request)
    await router.client.client.aclose()  # Close the client connection
    return response


# Example usage function for testing
async def test_router():
    """Test the router with a sample query"""
    # Set up a sample request
    request = RoutingRequest(
        refined_query="Recent advances in transformer architecture efficiency improvements",
        background=UserBackground(
            user_type="Specialized Professional",
            research_purpose="Staying updated on AI research developments",
            user_description="ML researcher focusing on NLP and transformer models",
            query_frequency="weekly"
        )
    )
    
    # Test Router0
    router = Router0()
    try:
        print("Testing Router0...")
        response = await router.route_query(request)
        
        print(f"Routing ID: {response.routing_id}")
        print("Search Guidance:")
        print(f"  Overall Strategy: {response.search_guidance.overall_strategy}")
        print(f"  Source Priorities: {response.search_guidance.source_priorities}")
        print(f"  Depth Guidance: {response.search_guidance.depth_guidance}")
        print(f"  Recency Guidance: {response.search_guidance.recency_guidance}")
        
        print("\nWeb Agent Context:")
        print(json.dumps(response.web_agent_context, indent=2))
        
        print("\nTwitter Agent Context:")
        print(json.dumps(response.twitter_agent_context, indent=2))
        
        if response.academic_agent_context:
            print("\nAcademic Agent Context:")
            print(json.dumps(response.academic_agent_context, indent=2))
            
    except Exception as e:
        print(f"Error testing Router0: {e}")
    finally:
        await router.client.client.aclose()
        
if __name__ == "__main__":
    try:
        asyncio.run(test_router())
    except KeyboardInterrupt:
        print("\nExiting router test.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
