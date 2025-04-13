"""Twitter Search Agent Module

This module implements an autonomous Twitter search agent that:
1. Discovers relevant expert profiles through web search
2. Constructs advanced Twitter queries
3. Handles thread expansion and analysis
4. Validates author credibility
5. Merges and ranks results
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import httpx
import traceback

# Constants
MAX_EXPERTS_TO_FIND = 25
MIN_EXPERT_SCORE = 0.7
MAX_TWEETS_PER_EXPERT = 50
DEFAULT_TIMEOUT = 30.0

class ExpertProfile(BaseModel):
    """A discovered expert profile"""
    username: str = Field(description="Twitter username")
    display_name: str = Field(description="Display name")
    bio: Optional[str] = Field(None, description="Profile bio")
    followers: Optional[int] = Field(None, description="Follower count")
    expertise_areas: List[str] = Field(description="Areas of expertise")
    credibility_score: float = Field(description="Computed credibility score")
    discovery_source: str = Field(description="How the expert was found")
    validation_signals: Dict[str, Any] = Field(description="Credibility signals")

class Tweet(BaseModel):
    """A processed tweet with metadata"""
    tweet_id: str = Field(description="Tweet ID")
    text: str = Field(description="Tweet text")
    author: str = Field(description="Author username")
    created_at: str = Field(description="Creation timestamp")
    retweet_count: Optional[int] = Field(None, description="Number of retweets")
    like_count: Optional[int] = Field(None, description="Number of likes")
    reply_count: Optional[int] = Field(None, description="Number of replies")
    quote_count: Optional[int] = Field(None, description="Number of quotes")
    is_retweet: bool = Field(description="Whether this is a retweet")
    is_quote: bool = Field(description="Whether this is a quote tweet")
    in_thread: bool = Field(description="Whether part of a thread")
    thread_id: Optional[str] = Field(None, description="ID of parent thread")
    urls: List[str] = Field(description="URLs mentioned")
    mentions: List[str] = Field(description="Users mentioned")
    hashtags: List[str] = Field(description="Hashtags used")

class Thread(BaseModel):
    """A Twitter thread"""
    thread_id: str = Field(description="Thread ID")
    author: str = Field(description="Thread author")
    tweets: List[Tweet] = Field(description="Tweets in thread")
    total_engagement: Dict[str, int] = Field(description="Aggregated engagement")
    summary: str = Field(description="Thread summary")
    key_points: List[str] = Field(description="Key points from thread")
    relevance_score: float = Field(description="Relevance to query")

class SearchQuery(BaseModel):
    """A Twitter advanced search query"""
    base_query: str = Field(description="Core search terms")
    authors: Optional[List[str]] = Field(None, description="Authors to include")
    exclude_authors: Optional[List[str]] = Field(None, description="Authors to exclude")
    min_replies: Optional[int] = Field(None, description="Minimum replies")
    min_retweets: Optional[int] = Field(None, description="Minimum retweets")
    min_likes: Optional[int] = Field(None, description="Minimum likes")
    since: Optional[str] = Field(None, description="Start date")
    until: Optional[str] = Field(None, description="End date")
    lang: str = Field(default="en", description="Language")
    filters: List[str] = Field(default_list=[], description="Additional filters")

class TwitterAgent:
    """
    Autonomous Twitter search agent that discovers experts and relevant content.
    
    The agent can:
    1. Use web search to find relevant Twitter experts
    2. Validate expert credibility through multiple signals
    3. Construct advanced search queries
    4. Process and expand threads
    5. Rank and filter results
    """
    
    def __init__(
        self,
        twitter_api_key: str,
        context: Dict[str, Any],
        web_search_key: Optional[str] = None
    ):
        """
        Initialize the Twitter agent.
        
        Args:
            twitter_api_key: Twitter API key for authentication
            context: Search context including query and user info
            web_search_key: Optional API key for web search (expert discovery)
        """
        self.twitter_api_key = twitter_api_key
        self.web_search_key = web_search_key
        self.context = context
        self.client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
        
        # Load Twitter search documentation
        with open("docs/twitter/SEARCH.md", "r") as f:
            self.search_docs = f.read()
            
        # Internal state
        self.discovered_experts: Dict[str, ExpertProfile] = {}
        self.found_threads: Dict[str, Thread] = {}
        self.found_tweets: Dict[str, Tweet] = {}
        self.seen_tweet_ids: Set[str] = set()
        self.quality_thresholds = {
            "min_expert_score": MIN_EXPERT_SCORE,
            "min_engagement": {
                "replies": 2,
                "retweets": 5,
                "likes": 10
            }
        }

    async def discover_experts(self, query: str) -> List[ExpertProfile]:
        """
        Use web search to discover relevant Twitter experts.
        
        Strategy:
        1. Search for "[topic] experts twitter"
        2. Look for Twitter lists, collection pages
        3. Find frequently cited experts
        4. Validate discovered profiles
        """
        experts = []
        
        try:
            # First try finding curated lists/collections
            list_results = await self._search_twitter_lists(query)
            for result in list_results:
                usernames = self._extract_usernames(result)
                for username in usernames:
                    if username not in self.discovered_experts:
                        profile = await self._validate_expert(username, query)
                        if profile and profile.credibility_score >= MIN_EXPERT_SCORE:
                            experts.append(profile)
                            self.discovered_experts[username] = profile
                            
            # Then try direct web search for experts
            search_results = await self._search_web_for_experts(query)
            for result in search_results:
                usernames = self._extract_usernames(result)
                for username in usernames:
                    if username not in self.discovered_experts:
                        profile = await self._validate_expert(username, query)
                        if profile and profile.credibility_score >= MIN_EXPERT_SCORE:
                            experts.append(profile)
                            self.discovered_experts[username] = profile
                            
        except Exception as e:
            print(f"Error discovering experts: {e}")
            traceback.print_exc()
            
        return experts

    async def _validate_expert(
        self,
        username: str,
        topic: str
    ) -> Optional[ExpertProfile]:
        """
        Validate a potential expert through multiple signals.
        
        Checks:
        1. Profile metrics (followers, following ratio)
        2. Bio relevance to topic
        3. Tweet history analysis
        4. External validation (mentions, citations)
        """
        try:
            # Get profile info
            profile = await self._get_twitter_profile(username)
            if not profile:
                return None
                
            # Basic metrics check
            if not self._check_basic_metrics(profile):
                return None
                
            # Analyze bio and tweets
            relevance_score = self._analyze_profile_relevance(profile, topic)
            engagement_score = await self._analyze_tweet_engagement(username)
            citation_score = await self._check_external_citations(username, topic)
            
            # Calculate overall score
            credibility_score = (
                relevance_score * 0.4 +
                engagement_score * 0.3 +
                citation_score * 0.3
            )
            
            if credibility_score < MIN_EXPERT_SCORE:
                return None
                
            # Create expert profile
            return ExpertProfile(
                username=username,
                display_name=profile.get("name", ""),
                bio=profile.get("description", ""),
                followers=profile.get("followers_count", 0),
                expertise_areas=self._extract_expertise_areas(profile, topic),
                credibility_score=credibility_score,
                discovery_source="profile_analysis",
                validation_signals={
                    "relevance_score": relevance_score,
                    "engagement_score": engagement_score,
                    "citation_score": citation_score,
                    "followers": profile.get("followers_count", 0),
                    "verified": profile.get("verified", False)
                }
            )
            
        except Exception as e:
            print(f"Error validating expert {username}: {e}")
            return None

    async def construct_search_queries(
        self,
        base_query: str,
        experts: List[ExpertProfile]
    ) -> List[SearchQuery]:
        """
        Construct multiple search queries based on discovered experts.
        
        Strategies:
        1. Expert-specific queries
        2. Topic-focused queries
        3. Time-based queries
        4. Engagement-filtered queries
        """
        queries = []
        
        # Base time range
        since_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Expert-specific queries
        for expert in experts[:MAX_EXPERTS_TO_FIND]:
            queries.append(SearchQuery(
                base_query=base_query,
                authors=[expert.username],
                min_replies=self.quality_thresholds["min_engagement"]["replies"],
                since=since_date,
                lang="en",
                filters=["filter:has_engagement", "-filter:retweets"]
            ))
            
        # Topic queries with engagement filters
        queries.append(SearchQuery(
            base_query=f"{base_query} filter:links",
            min_retweets=25,
            min_likes=100,
            since=since_date,
            lang="en",
            filters=["filter:has_engagement", "-filter:retweets"]
        ))
        
        # Recent developments query
        recent_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        queries.append(SearchQuery(
            base_query=f"{base_query} latest developments",
            since=recent_date,
            lang="en",
            filters=["filter:has_engagement", "-filter:retweets"]
        ))
        
        return queries

    async def execute_search_query(self, query: SearchQuery) -> List[Tweet]:
        """Execute a single search query and process results"""
        try:
            # Construct advanced search query
            search_query = self._build_advanced_query(query)
            
            # Execute search
            results = await self._search_twitter(search_query)
            
            # Process tweets
            tweets = []
            for result in results:
                tweet = self._process_tweet(result)
                if tweet and tweet.tweet_id not in self.seen_tweet_ids:
                    tweets.append(tweet)
                    self.seen_tweet_ids.add(tweet.tweet_id)
                    
                    # If it's a thread, expand it
                    if tweet.in_thread:
                        thread = await self._expand_thread(tweet)
                        if thread:
                            self.found_threads[thread.thread_id] = thread
                            
            return tweets
            
        except Exception as e:
            print(f"Error executing search query: {e}")
            traceback.print_exc()
            return []

    def _build_advanced_query(self, query: SearchQuery) -> str:
        """
        Build an advanced Twitter search query string.
        Uses the syntax documented in Twitter advanced search guide.
        """
        parts = [query.base_query]
        
        if query.authors:
            parts.extend(f"from:{author}" for author in query.authors)
            
        if query.exclude_authors:
            parts.extend(f"-from:{author}" for author in query.exclude_authors)
            
        if query.min_replies:
            parts.append(f"min_replies:{query.min_replies}")
            
        if query.min_retweets:
            parts.append(f"min_retweets:{query.min_retweets}")
            
        if query.min_likes:
            parts.append(f"min_faves:{query.min_likes}")
            
        if query.since:
            parts.append(f"since:{query.since}")
            
        if query.until:
            parts.append(f"until:{query.until}")
            
        if query.lang:
            parts.append(f"lang:{query.lang}")
            
        parts.extend(query.filters)
        
        return " ".join(parts)

    async def _expand_thread(self, tweet: Tweet) -> Optional[Thread]:
        """
        Expand a tweet thread by fetching all related tweets.
        
        Args:
            tweet: The tweet that's part of a thread
            
        Returns:
            Thread object if successful
        """
        try:
            # Get conversation ID
            conv_id = tweet.thread_id or tweet.tweet_id
            
            # Fetch conversation
            results = await self._get_conversation(conv_id)
            
            # Process tweets
            tweets = []
            total_engagement = {
                "replies": 0,
                "retweets": 0,
                "likes": 0,
                "quotes": 0
            }
            
            for result in results:
                thread_tweet = self._process_tweet(result)
                if thread_tweet:
                    tweets.append(thread_tweet)
                    # Update engagement
                    total_engagement["replies"] += thread_tweet.reply_count or 0
                    total_engagement["retweets"] += thread_tweet.retweet_count or 0
                    total_engagement["likes"] += thread_tweet.like_count or 0
                    total_engagement["quotes"] += thread_tweet.quote_count or 0
                    
            if tweets:
                # Create thread
                thread = Thread(
                    thread_id=conv_id,
                    author=tweets[0].author,
                    tweets=sorted(tweets, key=lambda t: t.created_at),
                    total_engagement=total_engagement,
                    summary=self._summarize_thread(tweets),
                    key_points=self._extract_thread_key_points(tweets),
                    relevance_score=self._calculate_thread_relevance(
                        tweets,
                        self.context.get("refined_query", "")
                    )
                )
                return thread
                
        except Exception as e:
            print(f"Error expanding thread {tweet.tweet_id}: {e}")
            
        return None

    def _summarize_thread(self, tweets: List[Tweet]) -> str:
        """Generate a concise summary of a thread"""
        # TODO: Implement more sophisticated summarization
        # For now, return first tweet text
        return tweets[0].text if tweets else ""

    def _extract_thread_key_points(self, tweets: List[Tweet]) -> List[str]:
        """Extract key points from a thread"""
        # TODO: Implement more sophisticated key point extraction
        # For now, return first 3 tweets
        return [t.text for t in tweets[:3]]

    def _calculate_thread_relevance(
        self,
        tweets: List[Tweet],
        query: str
    ) -> float:
        """Calculate thread relevance to query"""
        # TODO: Implement more sophisticated relevance calculation
        # For now, return 0.8 if query terms appear in first tweet
        query_terms = set(query.lower().split())
        first_tweet = tweets[0].text.lower() if tweets else ""
        matches = sum(1 for term in query_terms if term in first_tweet)
        return min(1.0, matches / len(query_terms)) if query_terms else 0.0

    async def execute_search_strategy(self) -> Dict[str, Any]:
        """
        Execute the full Twitter search strategy.
        
        Steps:
        1. Discover relevant experts
        2. Construct search queries
        3. Execute searches
        4. Process and expand threads
        5. Rank results
        
        Returns:
            Dict containing experts, threads, and individual tweets
        """
        stats = {"started": datetime.now().isoformat()}
        
        try:
            # Get refined query
            query = self.context.get("refined_query", "")
            
            # Discover experts first
            experts = await self.discover_experts(query)
            stats["experts_found"] = len(experts)
            
            # Construct search queries
            queries = await self.construct_search_queries(query, experts)
            stats["queries_planned"] = len(queries)
            
            # Execute all queries
            all_tweets = []
            for q in queries:
                tweets = await self.execute_search_query(q)
                all_tweets.extend(tweets)
                
            stats["tweets_found"] = len(all_tweets)
            stats["threads_found"] = len(self.found_threads)
            
            # Store non-thread tweets
            for tweet in all_tweets:
                if not tweet.in_thread:
                    self.found_tweets[tweet.tweet_id] = tweet
                    
            stats["completed"] = datetime.now().isoformat()
            
            return {
                "experts": self.discovered_experts,
                "threads": self.found_threads,
                "tweets": self.found_tweets,
                "statistics": stats
            }
            
        except Exception as e:
            print(f"Error in search strategy: {e}")
            traceback.print_exc()
            stats["error"] = str(e)
            stats["completed"] = datetime.now().isoformat()
            return {
                "experts": {},
                "threads": {},
                "tweets": {},
                "statistics": stats
            }