"""
Writing Context Router Module

This module implements Router0_4, which specializes in preparing context for the writing process 
by handling quality control, reranking, and source assignment for external data that has
been collected and cleaned.

The Router0_4 takes the output from data collection agents and transforms it into
an optimized structure for downstream writing modules by:
1. Performing quality control through reranking and filtering
2. Organizing sources into thematically coherent groups
3. Assigning sources to processing agents based on themes
4. Creating a rich context summary for writing modules
"""

import os, json
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from collections import Counter


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


class Router0_4:
    """
    Specialized router for writing preparation. It takes cleaned external sources,
    performs quality control through reranking and filtering, and organizes sources
    into thematically coherent groups for optimal writing context.
    
    This router preserves rich context while ensuring writing modules receive
    only high-quality, relevant information organized in a useful structure.
    
    Key responsibilities:
    1. Input Aggregation: Receives cleaned source dictionaries from upstream processes
    2. Quality Control: Filters low-quality sources and reranks based on relevance
    3. Thematic Organization: Clusters sources by topic for coherent context
    4. Agent Assignment: Distributes sources among processing agents by theme
    5. Context Sanitization: Prepares a clean, structured context for writing modules
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


# Example usage function for testing
async def test_router04():
    """Test the Router0_4 with sample data"""
    from datetime import datetime
    
    # Sample cleaned web sources
    web_sources = {
        "web_1": CleanedSource(
            metadata=SourceMetadata(
                source_id="web_1",
                source_type=SourceType.WEB,
                url="https://example.com/article1",
                title="Recent Advances in Transformer Efficiency",
                author="J. Smith",
                publication_date="2023-01-15",
                retrieved_date=datetime.now().strftime("%Y-%m-%d"),
                relevance_score=0.92,
                quality_score=0.88,
                content_snippet="This article discusses recent advances in transformer architecture efficiency..."
            ),
            content="Full content of article about transformer efficiency...",
            keywords=["transformers", "efficiency", "deep learning", "attention", "optimization"],
            relevance=SourceRelevance.HIGH
        ),
        "web_2": CleanedSource(
            metadata=SourceMetadata(
                source_id="web_2",
                source_type=SourceType.BLOG,
                url="https://example.com/blog2",
                title="Optimizing Transformer Inference",
                author="A. Johnson",
                publication_date="2023-02-20",
                retrieved_date=datetime.now().strftime("%Y-%m-%d"),
                relevance_score=0.85,
                quality_score=0.79,
                content_snippet="This blog post explains techniques for optimizing transformer inference..."
            ),
            content="Full content about transformer inference optimization...",
            keywords=["inference", "optimization", "transformers", "latency", "throughput"],
            relevance=SourceRelevance.HIGH
        ),
    }
    
    # Sample cleaned Twitter sources
    twitter_sources = {
        "twitter_1": CleanedSource(
            metadata=SourceMetadata(
                source_id="twitter_1",
                source_type=SourceType.TWITTER,
                url="https://twitter.com/user/status/123456",
                title=None,
                author="@ml_expert",
                publication_date="2023-03-05",
                retrieved_date=datetime.now().strftime("%Y-%m-%d"),
                relevance_score=0.75,
                quality_score=0.82,
                content_snippet="Just published our new paper on efficient transformer architectures..."
            ),
            content="Thread content about efficient transformer architectures...",
            keywords=["research", "transformers", "efficiency", "paper"],
            relevance=SourceRelevance.MEDIUM
        ),
    }
    
    # Sample user context
    user_context = {
        "refined_query": "Recent advances in transformer architecture efficiency improvements",
        "user_background": {
            "user_type": "Specialized Professional",
            "research_purpose": "Staying updated on AI research developments",
            "query_frequency": "weekly"
        }
    }
    
    # Create request
    request = WritingContextRequest(
        routing_id="sample_routing_id",
        cleaned_web_sources=web_sources,
        cleaned_twitter_sources=twitter_sources,
        user_context=user_context
    )
    
    try:
        print("Testing Router0_4...")
        response = await prepare_writing_context(request)
        
        print(f"Writing Context ID: {response.writing_context_id}")
        print(f"Refined Query: {response.refined_query}")
        print(f"Number of Reranked Sources: {len(response.reranked_sources)}")
        print(f"Number of Source Agents: {len(response.source_agents)}")
        print(f"Number of Thematic Clusters: {len(response.thematic_clusters)}")
        
        print("\nContext Summary:")
        print(f"  Top Topics: {response.context_summary.get('top_topics', [])}")
        print(f"  Structure Recommendation: {response.context_summary.get('writing_guidance', {}).get('structure_recommendation', '')}")
        
    except Exception as e:
        print(f"Error testing Router0_4: {e}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(test_router04())
    except KeyboardInterrupt:
        print("\nExiting router test.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()