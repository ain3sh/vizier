"""
Router Planning Flow Module

This module implements the core routing functionality for Vizier's research planning process.
It contains two primary router components:

1. Router0: Provides strategic guidance for external retrieval agents to find
   high-quality, relevant sources. Rather than dictating exact source counts,
   it focuses on communicating the key quality signals and exploration strategies.

2. Router0_4: Specializes in preparing context for the writing process by handling
   quality control, reranking, and source assignment for external data that has
   been collected and cleaned.

The Router Planning Flow ensures that both search and writing processes have
the optimal context to produce high-quality research output.
"""

import os, asyncio, json
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

# constants
DEFAULT_QUALITY_THRESHOLD = 0.6 # min quality score (0-1) to include a source
MIN_SOURCE_AGENTS = 3
MAX_SOURCE_AGENTS = 15


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

class SourceMetadata(BaseModel):
    """Metadata for an external source"""
    source_id: str = Field(description="Unique identifier for the source")
    source_type: SourceType = Field(description="Type of source")
    url: Optional[str] = Field(None, description="URL of the source if applicable")
    title: Optional[str] = Field(None, description="Title of the source")
    author: Optional[str] = Field(None, description="Author of the source")
    publication_date: Optional[str] = Field(None, description="Publication date of the source")
    retrieved_date: str = Field(description="Date when the source was retrieved")
    relevance_score: float = Field(description="Relevance score (0-1)")
    quality_score: float = Field(description="Quality score (0-1)")
    content_snippet: Optional[str] = Field(None, description="Brief snippet of the source content")

class CleanedSource(BaseModel):
    """A cleaned external source with content and metadata"""
    metadata: SourceMetadata = Field(description="Metadata about the source")
    content: str = Field(description="Cleaned content of the source")
    keywords: List[str] = Field(description="Extracted keywords from the source")
    relevance: SourceRelevance = Field(description="Assessed relevance to the query")


class SourceAgent(BaseModel):
    """Representation of a source processing agent"""
    agent_id: str = Field(description="Unique identifier for the agent")
    assigned_sources: List[str] = Field(description="List of source IDs assigned to this agent")
    source_types: List[SourceType] = Field(description="Types of sources assigned to this agent")
    priority: int = Field(description="Processing priority (lower = higher priority)")

class SourceExplorationStrategy(BaseModel):
    """Strategy guidance for exploring a particular source type"""
    source_type: SourceType = Field(description="Type of source to explore")
    importance: float = Field(description="Relative importance for this query (0-1)")
    key_signals: List[str] = Field(description="Signals of high-quality sources")
    depth_guidance: str = Field(description="Guidance on exploration depth")
    recency_guidance: str = Field(description="Guidance on source recency")
    authority_indicators: List[str] = Field(description="Indicators of authoritative sources")
    domain_specific_guidance: Optional[str] = Field(None, description="Domain-specific exploration guidance")


class RoutingRequest(BaseModel):
    """Request model for routing a refined query"""
    refined_query: str = Field(description="The refined query to route")
    background: UserBackground = Field(description="User background information")
    domain_context: Optional[Dict[str, Any]] = Field(None, description="Additional domain context")
    exploration_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences for exploration")

class RoutingResponse(BaseModel):
    """Response model for routing results"""
    routing_id: str = Field(description="Unique identifier for this routing operation")
    exploration_strategies: Dict[SourceType, SourceExplorationStrategy] = Field(
        description="Strategies for exploring different source types")
    agent_context: Dict[str, Any] = Field(description="Rich context for external retrieval agents")
    quality_signals: Dict[str, Any] = Field(description="Signals to evaluate source quality")


class WritingContextRequest(BaseModel):
    """Request model for preparing writing context"""
    routing_id: str = Field(description="ID of the initial routing operation")
    cleaned_web_sources: Dict[str, CleanedSource] = Field(description="Cleaned web sources")
    cleaned_twitter_sources: Dict[str, CleanedSource] = Field(description="Cleaned Twitter sources")
    user_context: Dict[str, Any] = Field(description="User context information")

class WritingContextResponse(BaseModel):
    """Response model with prepared writing context"""
    writing_context_id: str = Field(description="Unique identifier for this writing context")
    refined_query: str = Field(description="The refined query")
    reranked_sources: Dict[str, CleanedSource] = Field(description="Reranked and filtered sources")
    source_agents: Dict[str, SourceAgent] = Field(description="Source agents and their assignments")
    thematic_clusters: Dict[str, List[str]] = Field(description="Sources grouped by theme/topic")
    context_summary: Dict[str, Any] = Field(description="Summary of the writing context")


class Router0:
    """
    Strategic router that provides guidance for external data collection agents.

    Router0 focuses on providing rich context to guide dedicated retrieval agents
    to find the most valuable sources for deep analysis.
    """

    def __init__(self):
        """Initialize the Router0 instance"""
        pass

    def _generate_routing_id(self) -> str:
        """Generate a unique identifier for the routing operation"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = os.urandom(4).hex()
        return f"route_{timestamp}_{random_part}"

    def _extract_domain_keywords(self, query: str) -> List[str]:
        """
        Extract potential domain keywords from the query.

        Args:
            query: The refined query
            
        Returns:
            List of extracted domain keywords
        """
        # Simple extraction based on query text - in a real implementation,
        # this would use more sophisticated NLP techniques
        words = query.lower().split()
        # Filter out common words, focusing on potential domain terms
        domain_words = [w for w in words if len(w) > 3 and w not in 
                       {"the", "and", "for", "that", "with", "from", "about", "research",
                        "information", "analysis", "report", "study", "find", "search"}]
        return domain_words[:10]  # Return top potential domain keywords
    
    def _analyze_technical_depth(self, query: str, background: UserBackground) -> str:
        """
        Analyze the required technical depth based on query and user background.
        
        Args:
            query: The refined query
            background: User background information
            
        Returns:
            Technical depth assessment (high/medium/low)
        """
        # Default based on user type
        if background.user_type == "Specialized Professional":
            base_depth = "high"
        elif background.user_type == "Knowledge Worker":
            base_depth = "medium"
        else:
            base_depth = "medium"
        
        # Look for signals of technical depth requirements in query
        query_lower = query.lower()
        technical_signals = ["technical", "detailed", "in-depth", "comprehensive", 
                            "advanced", "specific", "specialized"]
        
        high_depth_signals = ["research paper", "whitepaper", "technical report", 
                             "academic", "journal", "scientific", "methodology",
                             "algorithm", "framework", "implementation"]
        
        # Adjust based on query content
        technical_count = sum(1 for signal in technical_signals if signal in query_lower)
        high_depth_count = sum(1 for signal in high_depth_signals if signal in query_lower)
        
        if high_depth_count >= 2 or technical_count >= 3:
            return "high"
        elif high_depth_count >= 1 or technical_count >= 2:
            return "medium-high"
        elif technical_count >= 1:
            return "medium"
        else:
            return base_depth
    
    def _determine_recency_importance(self, query: str, background: UserBackground) -> float:
        """
        Determine how important recency is for this query.
        
        Args:
            query: The refined query
            background: User background information
            
        Returns:
            Recency importance score (0-1)
        """
        # Base recency importance on query frequency
        base_recency = {
            "daily": 0.9,
            "weekly": 0.7,
            "monthly": 0.5
        }.get(background.query_frequency, 0.6)
        
        # Adjust based on query content
        query_lower = query.lower()
        recency_signals = ["recent", "latest", "new", "current", "emerging", "trend", 
                          "development", "update", "breakthrough"]
        
        recency_count = sum(1 for signal in recency_signals if signal in query_lower)
        
        # Adjust base recency by detected signals (max 0.95)
        return min(0.95, base_recency + (recency_count * 0.05))
    
    def _generate_exploration_strategies(
        self, 
        query: str, 
        background: UserBackground,
        domain_context: Optional[Dict[str, Any]] = None
    ) -> Dict[SourceType, SourceExplorationStrategy]:
        """
        Generate source exploration strategies based on query and user background.
        
        Args:
            query: The refined query
            background: User background information
            domain_context: Additional domain-specific context
            
        Returns:
            Dictionary mapping source types to exploration strategies
        """
        technical_depth = self._analyze_technical_depth(query, background)
        recency_importance = self._determine_recency_importance(query, background)
        domain_keywords = self._extract_domain_keywords(query)
        
        # Initialize strategies dictionary
        strategies = {}
        
        # Web Sources Strategy
        strategies[SourceType.WEB] = SourceExplorationStrategy(
            source_type=SourceType.WEB,
            importance=0.9,  # Web is almost always important
            key_signals=[
                "Comprehensive coverage of the topic",
                "Technical depth matching query requirements",
                "Authoritative sources",
                "Domain expertise evident in content",
                "Up-to-date information"
            ],
            depth_guidance=f"Seek {technical_depth} technical depth, prioritizing detailed explanations and analysis",
            recency_guidance=f"Prioritize content published within {'the last month' if recency_importance > 0.7 else 'the last year'}" if recency_importance > 0.5 else "Focus on foundational content with evergreen relevance",
            authority_indicators=[
                "Content from recognized experts or organizations",
                "Well-cited material",
                "Clear methodology and sources",
                "Technical accuracy and precision"
            ],
            domain_specific_guidance=f"Focus on content related to: {', '.join(domain_keywords)}"
        )
        
        # Academic Sources Strategy
        strategies[SourceType.ACADEMIC] = SourceExplorationStrategy(
            source_type=SourceType.ACADEMIC,
            importance=0.8 if technical_depth == "high" else 0.6,
            key_signals=[
                "Peer-reviewed research",
                "Citations from reputable researchers",
                "Methodological rigor",
                "Relevant to specific query aspects",
                "From recognized research institutions"
            ],
            depth_guidance="Prioritize detailed research with empirical findings or theoretical advancements",
            recency_guidance=f"Focus on research published within {'the last 6 months' if recency_importance > 0.8 else 'the last 2 years'}" if recency_importance > 0.5 else "Include seminal papers regardless of publication date",
            authority_indicators=[
                "High citation counts",
                "Reputable journal or conference",
                "Authors with established expertise",
                "Affiliation with leading research institutions"
            ],
            domain_specific_guidance=f"Seek papers connecting multiple concepts: {', '.join(domain_keywords[:3])}"
        )
        
        # Twitter Strategy
        strategies[SourceType.TWITTER] = SourceExplorationStrategy(
            source_type=SourceType.TWITTER,
            importance=0.7 if recency_importance > 0.7 else 0.5,
            key_signals=[
                "Posts from recognized experts",
                "Threads with technical substance",
                "Evidence-backed claims",
                "References to primary sources",
                "Discussion of recent developments"
            ],
            depth_guidance="Look for detailed threads rather than isolated posts",
            recency_guidance="Focus on content from the past 1-2 weeks for maximum relevance",
            authority_indicators=[
                "Verified accounts of domain experts",
                "Academic or professional credentials in profile",
                "History of quality content in the domain",
                "Engagement from other respected accounts"
            ],
            domain_specific_guidance=f"Search for discussions mentioning: {', '.join(domain_keywords)}"
        )
        
        # News Sources Strategy
        strategies[SourceType.NEWS] = SourceExplorationStrategy(
            source_type=SourceType.NEWS,
            importance=0.8 if recency_importance > 0.8 else 0.6,
            key_signals=[
                "Technical accuracy in reporting",
                "Expert interviews or quotes",
                "References to primary research",
                "Balanced coverage of developments",
                "Specialized tech/science publications"
            ],
            depth_guidance=f"{'Prioritize in-depth analysis over general news' if technical_depth == 'high' else 'Balance between accessible overview and technical details'}",
            recency_guidance="Focus on news from the past month for timely developments",
            authority_indicators=[
                "Reputable technical publications",
                "Specialized journalists with domain expertise",
                "Articles with cited sources",
                "Coverage from industry-specific outlets"
            ]
        )
        
        # Blog Sources Strategy
        strategies[SourceType.BLOG] = SourceExplorationStrategy(
            source_type=SourceType.BLOG,
            importance=0.7,
            key_signals=[
                "Written by recognized experts or practitioners",
                "Technical depth and insight",
                "Evidence and examples",
                "Practical applications or implementation details",
                "Engagement with current research"
            ],
            depth_guidance=f"{'Look for blogs with code examples, detailed explanations or benchmarks' if technical_depth == 'high' else 'Find blogs that bridge theory and practice'}",
            recency_guidance=f"{'Prioritize content from the past 3-6 months' if recency_importance > 0.6 else 'Focus on conceptual clarity regardless of publication date'}",
            authority_indicators=[
                "Author has relevant expertise or credentials",
                "Blog is respected within the community",
                "Content demonstrates hands-on experience",
                "References to research or authoritative sources"
            ]
        )
        
        return strategies
    
    def _prepare_quality_signals(self, technical_depth: str, recency_importance: float) -> Dict[str, Any]:
        """
        Prepare signals for evaluating source quality.
        
        Args:
            technical_depth: Required technical depth
            recency_importance: Importance of recency
            
        Returns:
            Dictionary of quality signals
        """
        return {
            "technical_depth": {
                "requirement": technical_depth,
                "signals": {
                    "high": [
                        "Detailed technical explanations",
                        "Methodology descriptions",
                        "Implementation details",
                        "Empirical evidence or data",
                        "Mathematical or theoretical foundations",
                        "Comparison of approaches"
                    ],
                    "medium": [
                        "Clear explanations of concepts",
                        "Some technical details",
                        "Practical applications",
                        "Case studies or examples",
                        "References to more detailed sources"
                    ],
                    "low": [
                        "Overview of concepts",
                        "Minimal technical jargon",
                        "Focus on implications rather than mechanisms",
                        "Simplified explanations"
                    ]
                }
            },
            "authority": {
                "importance": 0.8,
                "signals": [
                    "Author expertise and credentials",
                    "Institutional affiliation",
                    "Citation or reference quality",
                    "Recognition within the field",
                    "Methodological rigor",
                    "Peer review or editorial oversight"
                ]
            },
            "recency": {
                "importance": recency_importance,
                "preferences": {
                    "very_high": "Within last month",
                    "high": "Within last 6 months",
                    "medium": "Within last year",
                    "low": "Within last 3 years",
                    "very_low": "Any time period"
                },
                "current_preference": "very_high" if recency_importance > 0.8 else
                                     "high" if recency_importance > 0.6 else
                                     "medium" if recency_importance > 0.4 else
                                     "low" if recency_importance > 0.2 else
                                     "very_low"
            },
            "comprehensiveness": {
                "importance": 0.7,
                "signals": [
                    "Covers multiple aspects of the topic",
                    "Addresses related concepts",
                    "Discusses limitations or alternatives",
                    "Provides context and background",
                    "Connects to broader field or applications"
                ]
            }
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
        
        # Analyze query for technical depth and recency importance
        technical_depth = self._analyze_technical_depth(request.refined_query, request.background)
        recency_importance = self._determine_recency_importance(request.refined_query, request.background)
        
        # Generate exploration strategies for different source types
        exploration_strategies = self._generate_exploration_strategies(
            request.refined_query, 
            request.background,
            request.domain_context
        )
        
        # Prepare quality signals
        quality_signals = self._prepare_quality_signals(technical_depth, recency_importance)
        
        # Prepare context for external retrieval agents
        agent_context = {
            "refined_query": request.refined_query,
            "user_background": request.background.dict(),
            "technical_depth": technical_depth,
            "recency_importance": recency_importance,
            "domain_keywords": self._extract_domain_keywords(request.refined_query),
            "exploration_scope": {
                "breadth": "Prioritize finding diverse perspectives and complementary information sources",
                "depth": f"Seek {technical_depth} technical depth appropriate for {request.background.user_type}",
                "recency_preference": "high" if recency_importance > 0.7 else "medium",
                "authority_emphasis": "high" if technical_depth == "high" else "medium",
                "practical_vs_theoretical": "balanced" if technical_depth == "medium" else 
                                          "theoretical" if technical_depth == "high" else "practical"
            }
        }
        
        # Add domain-specific context if available
        if request.domain_context:
            agent_context["domain_context"] = request.domain_context
            
        # Add exploration preferences if available
        if request.exploration_preferences:
            agent_context["exploration_preferences"] = request.exploration_preferences
        
        return RoutingResponse(
            routing_id=routing_id,
            exploration_strategies={
                source_type: strategy for source_type, strategy in exploration_strategies.items()
            },
            agent_context=agent_context,
            quality_signals=quality_signals
        )


class Router0_4:
    """
    Specialized router for writing preparation. It takes cleaned external sources,
    performs quality control through reranking and filtering, and organizes sources
    into thematically coherent groups for optimal writing context.
    
    This router preserves rich context while ensuring writing modules receive
    only high-quality, relevant information organized in a useful structure.
    """
    
    def __init__(
        self,
        cleaned_web_sources: Dict[str, CleanedSource],
        cleaned_twitter_sources: Dict[str, CleanedSource],
        user_context: Dict[str, Any],
        quality_threshold: float = DEFAULT_QUALITY_THRESHOLD
    ):
        """
        Initialize the Router0_4 instance.
        
        Args:
            cleaned_web_sources: Dictionary of cleaned web sources
            cleaned_twitter_sources: Dictionary of cleaned Twitter sources
            user_context: User context information including refined query
            quality_threshold: Minimum quality score to include a source
        """
        self.cleaned_web_sources = cleaned_web_sources
        self.cleaned_twitter_sources = cleaned_twitter_sources
        self.user_context = user_context
        self.quality_threshold = quality_threshold
        self.reranked_sources = None
        self.assigned_agents = None
        self.thematic_clusters = None
        
    def _generate_writing_context_id(self) -> str:
        """Generate a unique identifier for the writing context"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = os.urandom(4).hex()
        return f"write_{timestamp}_{random_part}"
    
    def _extract_thematic_keywords(self, source: CleanedSource) -> List[str]:
        """
        Extract thematic keywords from a source.
        
        Args:
            source: The source to analyze
            
        Returns:
            List of thematic keywords
        """
        # Start with source's own keywords
        keywords = source.keywords.copy() if source.keywords else []
        
        # Add title words if available
        if source.metadata.title:
            title_words = [word.lower() for word in source.metadata.title.split() 
                          if len(word) > 3 and word.lower() not in ["the", "and", "for"]]
            keywords.extend(title_words)
            
        # Extract from content snippet if available
        if source.metadata.content_snippet:
            snippet_words = [word.lower() for word in source.metadata.content_snippet.split() 
                            if len(word) > 4 and word.lower() not in ["the", "and", "for", "that", "with"]]
            # Take the most frequent words from the snippet
            from collections import Counter
            word_counts = Counter(snippet_words)
            top_words = [word for word, _ in word_counts.most_common(5)]
            keywords.extend(top_words)
            
        # Remove duplicates and return
        unique_keywords = list(set(keywords))
        return unique_keywords[:10]  # Limit to top 10 keywords
    
    def rerank_sources(self) -> Dict[str, CleanedSource]:
        """
        Rerank and filter sources based on relevance, quality and complementary value.
        
        This prioritizes high-quality sources while ensuring diversity of information
        and complementary perspectives.
        
        Returns:
            Dictionary of reranked and filtered sources
        """
        # Combine web and Twitter sources
        combined_sources = {**self.cleaned_web_sources, **self.cleaned_twitter_sources}
        
        # Filter out low-quality sources
        filtered_sources = {
            source_id: source 
            for source_id, source in combined_sources.items()
            if source.metadata.quality_score >= self.quality_threshold
        }
        
        # Extract refined query from user context
        refined_query = self.user_context.get("refined_query", "")
        
        # Create a scoring function that considers relevance, quality, and information diversity
        def source_score(source: CleanedSource) -> float:
            # Base weights
            relevance_weight = 0.6
            quality_weight = 0.3
            diversity_weight = 0.1
            
            # Convert relevance enum to numeric score
            relevance_numeric = {
                SourceRelevance.HIGH: 1.0,
                SourceRelevance.MEDIUM: 0.7,
                SourceRelevance.LOW: 0.4,
                SourceRelevance.IRRELEVANT: 0.0
            }.get(source.relevance, 0.0)
            
            # Calculate keyword overlap with query as a diversity signal
            query_words = set([w.lower() for w in refined_query.split() if len(w) > 3])
            source_keywords = set([k.lower() for k in self._extract_thematic_keywords(source)])
            
            # Unique keywords that aren't in the query indicate information diversity
            unique_keywords = source_keywords - query_words
            diversity_score = min(1.0, len(unique_keywords) / 5.0)  # Scale to 0-1
            
            # Calculate weighted score
            return (
                relevance_weight * relevance_numeric + 
                quality_weight * source.metadata.quality_score +
                diversity_weight * diversity_score
            )
        
        # Score and sort sources
        source_scores = {source_id: source_score(source) for source_id, source in filtered_sources.items()}
        
        # Rerank sources based on scores
        sorted_sources = dict(
            sorted(
                filtered_sources.items(), 
                key=lambda item: source_scores.get(item[0], 0),
                reverse=True
            )
        )
        
        self.reranked_sources = sorted_sources
        return sorted_sources
    
    def _cluster_sources_by_theme(self) -> Dict[str, List[str]]:
        """
        Group sources into thematic clusters based on keyword similarity.
        
        Returns:
            Dictionary mapping themes to lists of source IDs
        """
        if not self.reranked_sources:
            self.rerank_sources()
        
        # Extract keywords for each source
        source_keywords = {
            source_id: set(self._extract_thematic_keywords(source))
            for source_id, source in self.reranked_sources.items()
        }
        
        # Find common themes across sources
        all_keywords = set()
        for keywords in source_keywords.values():
            all_keywords.update(keywords)
        
        # Create thematic clusters
        themes = {}
        
        # Group by keyword overlap
        for keyword in all_keywords:
            # Find sources that contain this keyword
            sources_with_keyword = [
                source_id for source_id, keywords in source_keywords.items()
                if keyword in keywords
            ]
            
            if len(sources_with_keyword) > 1:  # Only create themes with multiple sources
                themes[keyword] = sources_with_keyword
        
        # Consolidate overlapping themes
        consolidated_themes = {}
        processed_themes = set()
        
        for theme, sources in sorted(themes.items(), key=lambda x: len(x[1]), reverse=True):
            if theme in processed_themes:
                continue
                
            # Find overlapping themes
            overlapping = [
                t for t in themes
                if t != theme and not t in processed_themes and 
                len(set(themes[t]) & set(sources)) / len(themes[t]) > 0.5
            ]
            
            # Mark as processed
            processed_themes.add(theme)
            for t in overlapping:
                processed_themes.add(t)
            
            # Create consolidated theme
            if overlapping:
                theme_name = f"{theme}+{len(overlapping)}"
                consolidated_sources = set(sources)
                for t in overlapping:
                    consolidated_sources.update(themes[t])
                consolidated_themes[theme_name] = list(consolidated_sources)
            else:
                consolidated_themes[theme] = sources
        
        self.thematic_clusters = consolidated_themes
        return consolidated_themes
        
    def assign_source_agents(self) -> Dict[str, SourceAgent]:
        """
        Assign sources to agents based on thematic clusters rather than
        simple mechanical distribution.
        
        Returns:
            Dictionary mapping agent IDs to SourceAgent objects
        """
        if not self.reranked_sources:
            self.rerank_sources()
            
        if not self.thematic_clusters:
            self._cluster_sources_by_theme()
            
        # Determine how many agents we need based on thematic clustering
        theme_count = len(self.thematic_clusters)
        agent_count = max(
            MIN_SOURCE_AGENTS, 
            min(MAX_SOURCE_AGENTS, (theme_count + 1) // 2)
        )
        
        # Create empty agents
        agents = {
            f"agent_{i+1}": SourceAgent(
                agent_id=f"agent_{i+1}",
                assigned_sources=[],
                source_types=[],
                priority=i+1
            )
            for i in range(agent_count)
        }
        
        # Sort themes by size (number of sources)
        sorted_themes = sorted(
            self.thematic_clusters.items(),
            key=lambda item: len(item[1]),
            reverse=True
        )
        
        # Assign entire themes to agents, distributing by theme size
        agent_keys = list(agents.keys())
        current_theme_sizes = {agent_key: 0 for agent_key in agent_keys}
        
        for theme, sources in sorted_themes:
            # Find agent with lowest current workload
            target_agent_key = min(
                current_theme_sizes.items(),
                key=lambda x: x[1]
            )[0]
            
            # Assign all sources in this theme to the agent
            agent = agents[target_agent_key]
            agent.assigned_sources.extend(sources)
            
            # Update agent source types
            for source_id in sources:
                if source_id in self.reranked_sources:
                    source_type = self.reranked_sources[source_id].metadata.source_type
                    if source_type not in agent.source_types:
                        agent.source_types.append(source_type)
            
            # Update theme size counter for this agent
            current_theme_sizes[target_agent_key] += len(sources)
        
        self.assigned_agents = agents
        return agents
        
    def _prepare_context_summary(self) -> Dict[str, Any]:
        """
        Prepare a rich context summary for the writing module.
        
        Unlike the previous implementation, this preserves valuable context
        while organizing it in a structured way for optimal writing.
        
        Returns:
            Dictionary containing the writing context summary
        """
        if not self.reranked_sources:
            self.rerank_sources()
            
        if not self.assigned_agents:
            self.assign_source_agents()
            
        if not self.thematic_clusters:
            self._cluster_sources_by_theme()
            
        # Extract the refined query
        refined_query = self.user_context.get("refined_query", "")
        
        # Extract key topics from the sources
        all_keywords = []
        for source in self.reranked_sources.values():
            all_keywords.extend(source.keywords)
        
        from collections import Counter
        keyword_counter = Counter(all_keywords)
        top_topics = [topic for topic, _ in keyword_counter.most_common(10)]
        
        # Create source summaries with rich context
        source_summaries = {}
        for source_id, source in self.reranked_sources.items():
            source_summaries[source_id] = {
                "title": source.metadata.title,
                "source_type": source.metadata.source_type,
                "url": source.metadata.url,
                "author": source.metadata.author,
                "publication_date": source.metadata.publication_date,
                "relevance": source.relevance,
                "quality_score": source.metadata.quality_score,
                "content_snippet": source.metadata.content_snippet,
                "keywords": source.keywords,
                # Find which themes this source belongs to
                "themes": [
                    theme for theme, sources in self.thematic_clusters.items()
                    if source_id in sources
                ]
            }
        
        # Analyze source composition
        source_type_counts = {}
        for source in self.reranked_sources.values():
            source_type = source.metadata.source_type
            source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
        
        # Create a summary of the agent assignments
        agent_summaries = {}
        for agent_id, agent in self.assigned_agents.items():
            # Find which themes this agent is responsible for
            agent_themes = []
            for theme, sources in self.thematic_clusters.items():
                if any(source_id in agent.assigned_sources for source_id in sources):
                    agent_themes.append(theme)
            
            agent_summaries[agent_id] = {
                "source_count": len(agent.assigned_sources),
                "assigned_sources": agent.assigned_sources,
                "source_types": agent.source_types,
                "priority": agent.priority,
                "themes": agent_themes
            }
        
        # Create the context summary
        context_summary = {
            "refined_query": refined_query,
            "top_topics": top_topics,
            "source_composition": source_type_counts,
            "sources": source_summaries,
            "thematic_clusters": self.thematic_clusters,
            "source_agents": agent_summaries,
            "user_context": {
                "user_type": self.user_context.get("user_background", {}).get("user_type", ""),
                "research_purpose": self.user_context.get("user_background", {}).get("research_purpose", ""),
                "query_frequency": self.user_context.get("user_background", {}).get("query_frequency", "")
            },
            "writing_guidance": {
                "structure_recommendation": "thematic" if len(self.thematic_clusters) >= 3 else "source_type",
                "technical_depth": "high" if self.user_context.get("user_background", {}).get("user_type", "") == "Specialized Professional" else "medium",
                "emphasis": top_topics[:3] if top_topics else []
            }
        }
        
        return context_summary
        
    async def prepare_writing_context(self) -> WritingContextResponse:
        """
        Execute the full Router0_4 workflow to prepare a rich, organized context
        for the writing module.
        
        Returns:
            WritingContextResponse with the prepared writing context
        """
        # Generate a unique writing context ID
        writing_context_id = self._generate_writing_context_id()
        
        # Run the reranking and filtering
        self.rerank_sources()
        
        # Cluster sources by theme
        self._cluster_sources_by_theme()
        
        # Assign sources to agents
        self.assign_source_agents()
        
        # Create rich context summary
        context_summary = self._prepare_context_summary()
        
        # Extract refined query
        refined_query = self.user_context.get("refined_query", "")
        
        return WritingContextResponse(
            writing_context_id=writing_context_id,
            refined_query=refined_query,
            reranked_sources=self.reranked_sources,
            source_agents=self.assigned_agents,
            thematic_clusters=self.thematic_clusters,
            context_summary=context_summary
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
    return await router.route_query(request)

async def prepare_writing_context(request: WritingContextRequest) -> WritingContextResponse:
    """
    API endpoint for preparing writing context from cleaned sources.
    
    Args:
        request: The writing context request
        
    Returns:
        WritingContextResponse with prepared writing context
    """
    router = Router0_4(
        request.cleaned_web_sources,
        request.cleaned_twitter_sources,
        request.user_context
    )
    return await router.prepare_writing_context()
