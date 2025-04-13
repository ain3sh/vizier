"""Web Search Agent Module

This module implements an autonomous web search agent that:
1. Plans and executes Perplexica searches
2. Validates sources and extracts metadata
3. Ranks and filters results
4. Handles academic and technical content discovery
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from pydantic import BaseModel, Field
import httpx
from urllib.parse import urlparse
import traceback

# Constants
DEFAULT_TIMEOUT = 30.0
MIN_QUALITY_SCORE = 0.6
MAX_DEPTH = 3  # Max depth for following related links

class WebSource(BaseModel):
    """A processed web source with metadata"""
    url: str = Field(description="Source URL")
    title: str = Field(description="Page title")
    author: Optional[str] = Field(None, description="Author if available")
    date_published: Optional[str] = Field(None, description="Publication date")
    date_retrieved: str = Field(description="Retrieval timestamp")
    content_type: str = Field(description="Content type (article, paper, etc)")
    domain: str = Field(description="Source domain")
    content_snippet: str = Field(description="Brief content preview")
    keywords: List[str] = Field(description="Extracted keywords")
    quality_signals: Dict[str, Any] = Field(description="Quality indicators")
    credibility_score: float = Field(description="Computed credibility")
    relevance_score: float = Field(description="Relevance to query")
    depth: int = Field(description="Discovery depth (0 = direct result)")

class SearchIntent(BaseModel):
    """Search intent and parameters"""
    query: str = Field(description="Core search query")
    focus: str = Field(description="Search focus (academic/technical/news)")
    time_range: Optional[str] = Field(None, description="Time range constraint")
    required_terms: List[str] = Field(description="Must-include terms")
    excluded_terms: List[str] = Field(description="Must-exclude terms")
    domain_filters: Optional[List[str]] = Field(None, description="Allowed domains")

class PerplexicaConfig(BaseModel):
    """Perplexica API configuration"""
    chat_model: Dict[str, str] = Field(description="Chat model settings")
    embedding_model: Dict[str, str] = Field(description="Embedding model settings")
    optimization_mode: str = Field(description="Speed vs quality tradeoff")
    focus_mode: str = Field(description="Search focus mode")
    stream: bool = Field(description="Whether to stream results")

class WebAgent:
    """
    Autonomous web search agent powered by Perplexica.
    
    Features:
    1. Intelligent query planning and execution
    2. Source validation and credibility scoring
    3. Content type detection and processing
    4. Related content discovery
    5. Academic and technical focus modes
    """
    
    def __init__(
        self,
        perplexica_api_key: str,
        context: Dict[str, Any]
    ):
        """
        Initialize the web search agent.
        
        Args:
            perplexica_api_key: Perplexica API key
            context: Search context with query and user info
        """
        self.api_key = perplexica_api_key
        self.context = context
        self.client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
        
        # Load Perplexica docs
        with open("docs/perplexica/SEARCH.md", "r") as f:
            self.perplexica_docs = f.read()
            
        # Internal state
        self.found_sources: Dict[str, WebSource] = {}
        self.seen_urls: Set[str] = set()
        self.search_stats: Dict[str, Any] = {
            "queries_executed": 0,
            "sources_found": 0,
            "sources_filtered": 0
        }
        
    def _plan_search_strategy(self) -> List[SearchIntent]:
        """
        Plan multiple search intents based on query and context.
        
        Returns:
            List of SearchIntent objects
        """
        query = self.context.get("refined_query", "")
        user_background = self.context.get("user_background", {})
        
        intents = []
        
        # Core technical search
        intents.append(SearchIntent(
            query=query,
            focus="technical",
            required_terms=self._extract_key_terms(query),
            excluded_terms=[],
            time_range="1y"  # Default to last year
        ))
        
        # Academic focus for specialized users
        if user_background.get("user_type") == "Specialized Professional":
            academic_query = f"{query} research paper"
            intents.append(SearchIntent(
                query=academic_query,
                focus="academic",
                required_terms=["paper", "research", "study"],
                excluded_terms=[],
                domain_filters=[".edu", ".org", "arxiv.org", "scholar.google.com"]
            ))
            
        # Recent developments
        recent_query = f"{query} latest developments"
        intents.append(SearchIntent(
            query=recent_query,
            focus="news",
            time_range="3m",  # Last 3 months
            required_terms=["new", "latest", "recent"],
            excluded_terms=[]
        ))
        
        return intents

    def _extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from query for required terms"""
        # TODO: Implement more sophisticated term extraction
        # For now, just split and filter common words
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to"}
        return [word for word in query.lower().split() 
                if word not in common_words and len(word) > 2]

    async def execute_perplexica_search(
        self,
        intent: SearchIntent
    ) -> List[Dict[str, Any]]:
        """
        Execute a search using Perplexica's API.
        
        Args:
            intent: Search intent to execute
            
        Returns:
            List of raw search results
        """
        try:
            # Configure Perplexica
            config = PerplexicaConfig(
                chat_model={
                    "provider": "openai",
                    "name": "gpt-4o-mini"  # Using mini for speed
                },
                embedding_model={
                    "provider": "openai",
                    "name": "text-embedding-3-large"
                },
                optimization_mode="balanced",
                focus_mode=self._map_intent_to_focus(intent.focus),
                stream=False
            )
            
            # Build search payload
            payload = {
                "query": intent.query,
                "chatModel": config.chat_model,
                "embeddingModel": config.embedding_model,
                "optimizationMode": config.optimization_mode,
                "focusMode": config.focus_mode
            }
            
            # Add time range if specified
            if intent.time_range:
                payload["timeRange"] = intent.time_range
                
            # Execute search
            async with self.client.post(
                "http://localhost:3000/api/search",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    self.search_stats["queries_executed"] += 1
                    return data.get("sources", [])
                else:
                    print(f"Perplexica search failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Error in Perplexica search: {e}")
            traceback.print_exc()
            return []

    def _map_intent_to_focus(self, intent_focus: str) -> str:
        """Map search intent focus to Perplexica focus mode"""
        focus_map = {
            "technical": "webSearch",
            "academic": "academicSearch",
            "news": "webSearch"  # Default to web search for news
        }
        return focus_map.get(intent_focus, "webSearch")

    async def process_source(
        self,
        raw_source: Dict[str, Any],
        intent: SearchIntent,
        depth: int = 0
    ) -> Optional[WebSource]:
        """
        Process and validate a single source.
        
        Args:
            raw_source: Raw source data from Perplexica
            intent: Original search intent
            depth: Discovery depth (0 = direct result)
            
        Returns:
            WebSource object if valid, None if filtered out
        """
        try:
            url = raw_source.get("metadata", {}).get("url")
            if not url or url in self.seen_urls:
                return None
                
            self.seen_urls.add(url)
            
            # Extract metadata
            domain = urlparse(url).netloc
            content_type = self._detect_content_type(raw_source)
            
            # Compute quality signals
            quality_signals = self._compute_quality_signals(raw_source, domain)
            credibility_score = self._calculate_credibility(quality_signals)
            
            if credibility_score < MIN_QUALITY_SCORE:
                return None
                
            # Create source object
            source = WebSource(
                url=url,
                title=raw_source.get("metadata", {}).get("title", ""),
                author=raw_source.get("metadata", {}).get("author"),
                date_published=raw_source.get("metadata", {}).get("date"),
                date_retrieved=datetime.now().isoformat(),
                content_type=content_type,
                domain=domain,
                content_snippet=raw_source.get("pageContent", "")[:500],
                keywords=self._extract_keywords(raw_source),
                quality_signals=quality_signals,
                credibility_score=credibility_score,
                relevance_score=self._calculate_relevance(
                    raw_source,
                    intent.query,
                    intent.required_terms
                ),
                depth=depth
            )
            
            self.search_stats["sources_found"] += 1
            return source
            
        except Exception as e:
            print(f"Error processing source {url}: {e}")
            return None

    def _detect_content_type(self, source: Dict[str, Any]) -> str:
        """Detect the type of content (article, paper, etc)"""
        url = source.get("metadata", {}).get("url", "").lower()
        content = source.get("pageContent", "").lower()
        
        if any(d in url for d in [".edu", "arxiv.org", "scholar.google"]):
            return "academic"
        elif any(term in content for term in ["paper", "research", "study", "journal"]):
            return "paper"
        elif "github.com" in url:
            return "code"
        elif any(d in url for d in ["blog.", ".blog", "medium.com"]):
            return "blog"
        else:
            return "article"

    def _compute_quality_signals(
        self,
        source: Dict[str, Any],
        domain: str
    ) -> Dict[str, Any]:
        """Compute various quality signals for a source"""
        signals = {
            "domain_authority": self._get_domain_authority(domain),
            "content_length": len(source.get("pageContent", "")),
            "has_references": "references" in source.get("pageContent", "").lower(),
            "reading_level": self._estimate_reading_level(source.get("pageContent", "")),
            "technical_depth": self._estimate_technical_depth(source)
        }
        return signals

    def _get_domain_authority(self, domain: str) -> float:
        """Estimate domain authority (placeholder)"""
        # TODO: Implement real domain authority checking
        edu_bonus = 0.2 if ".edu" in domain else 0
        org_bonus = 0.1 if ".org" in domain else 0
        return 0.7 + edu_bonus + org_bonus

    def _estimate_reading_level(self, content: str) -> float:
        """Estimate content reading level (placeholder)"""
        # TODO: Implement sophisticated reading level analysis
        return 0.8  # Default to moderately complex

    def _estimate_technical_depth(self, source: Dict[str, Any]) -> float:
        """Estimate technical depth of content (placeholder)"""
        # TODO: Implement real technical depth analysis
        return 0.7  # Default to moderately technical

    def _calculate_credibility(self, signals: Dict[str, Any]) -> float:
        """Calculate overall credibility score from signals"""
        weights = {
            "domain_authority": 0.4,
            "content_length": 0.1,
            "has_references": 0.2,
            "reading_level": 0.15,
            "technical_depth": 0.15
        }
        
        score = sum(
            signals.get(signal, 0) * weight
            for signal, weight in weights.items()
        )
        
        return min(1.0, max(0.0, score))

    def _calculate_relevance(
        self,
        source: Dict[str, Any],
        query: str,
        required_terms: List[str]
    ) -> float:
        """Calculate relevance score for a source"""
        content = source.get("pageContent", "").lower()
        title = source.get("metadata", {}).get("title", "").lower()
        
        # Check required terms
        if not all(term.lower() in content or term.lower() in title 
                  for term in required_terms):
            return 0.0
            
        # Simple term frequency for now
        query_terms = set(query.lower().split())
        matches_title = sum(1 for term in query_terms if term in title)
        matches_content = sum(1 for term in query_terms if term in content)
        
        # Weight title matches more heavily
        score = (matches_title * 2 + matches_content) / (len(query_terms) * 3)
        return min(1.0, score)

    def _extract_keywords(self, source: Dict[str, Any]) -> List[str]:
        """Extract keywords from source content"""
        # TODO: Implement more sophisticated keyword extraction
        # For now return any provided keywords or empty list
        return source.get("metadata", {}).get("keywords", [])

    async def discover_related_content(
        self,
        source: WebSource,
        intent: SearchIntent,
        depth: int
    ) -> List[WebSource]:
        """
        Discover content related to a source through links.
        
        Args:
            source: Original source
            intent: Search intent
            depth: Current depth
            
        Returns:
            List of related sources
        """
        if depth >= MAX_DEPTH:
            return []
            
        related = []
        try:
            # Get page content
            async with self.client.get(source.url) as response:
                if response.status_code != 200:
                    return []
                    
                content = response.text
                
            # Extract links
            links = self._extract_links(content, source.url)
            
            # Process each link
            for link in links[:5]:  # Limit to top 5 links
                if link not in self.seen_urls:
                    # Fetch and process linked page
                    async with self.client.get(link) as response:
                        if response.status_code == 200:
                            raw_source = {
                                "metadata": {
                                    "url": link,
                                    "title": self._extract_title(response.text)
                                },
                                "pageContent": response.text
                            }
                            
                            related_source = await self.process_source(
                                raw_source,
                                intent,
                                depth + 1
                            )
                            
                            if related_source:
                                related.append(related_source)
                                
        except Exception as e:
            print(f"Error discovering related content: {e}")
            
        return related

    def _extract_links(self, content: str, base_url: str) -> List[str]:
        """Extract and normalize links from HTML content"""
        # TODO: Implement proper HTML parsing
        # For now return empty list
        return []

    def _extract_title(self, content: str) -> str:
        """Extract title from HTML content"""
        # TODO: Implement proper HTML parsing
        # For now return empty string
        return ""

    async def execute_search_strategy(self) -> Dict[str, Any]:
        """
        Execute the full web search strategy.
        
        Steps:
        1. Plan search intents
        2. Execute Perplexica searches
        3. Process and validate sources
        4. Discover related content
        5. Rank results
        
        Returns:
            Dict containing found sources and statistics
        """
        stats = {"started": datetime.now().isoformat()}
        
        try:
            # Plan search strategy
            intents = self._plan_search_strategy()
            stats["intents_planned"] = len(intents)
            
            # Execute all intents
            for intent in intents:
                # Search with Perplexica
                results = await self.execute_perplexica_search(intent)
                
                # Process sources
                for result in results:
                    source = await self.process_source(result, intent)
                    if source:
                        self.found_sources[source.url] = source
                        
                        # Discover related content if depth allows
                        if len(self.found_sources) < 50:  # Limit total sources
                            related = await self.discover_related_content(
                                source,
                                intent,
                                depth=0
                            )
                            
                            # Add related sources
                            for rel in related:
                                if rel.url not in self.found_sources:
                                    self.found_sources[rel.url] = rel
                                    
            stats.update(self.search_stats)
            stats["completed"] = datetime.now().isoformat()
            
            return {
                "sources": self.found_sources,
                "statistics": stats
            }
            
        except Exception as e:
            print(f"Error in search strategy: {e}")
            traceback.print_exc()
            stats["error"] = str(e)
            stats["completed"] = datetime.now().isoformat()
            return {
                "sources": {},
                "statistics": stats
            }