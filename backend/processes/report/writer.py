"""
Writer Module

This module implements the Writer agent for Vizier's report generation process. 
It transforms high-quality source data from upstream source agents into 
comprehensive research reports through an iterative refinement loop.

The process follows this flow:
1. System receives consolidated source data from Router_04
2. Writer agent synthesizes an initial comprehensive draft
3. User provides feedback on the draft report
4. Writer agent incorporates feedback to produce an improved report
5. Loop continues until user approves the final report
6. Final approved report is returned

This component follows the source exploration and filtering stages, ensuring
that only high-quality, relevant information is used in the final report.
"""

import os, asyncio, json
from typing import Dict, List, Optional, Any, Callable, TypedDict, Literal
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, TypeAdapter
from routers.openrouter import OpenRouterClient
from sourcing.director import SourceDirector, DirectorResponse
from sourcing.agent import SourceAgent

# constants
WRITER_MODEL = "openrouter/anthropic/claude-3-opus"
MAX_TOKENS_INTERNAL = 100000  # For internal drafts and processing
MAX_TOKENS_DRAFT = 100000     # For user-facing drafts
TEMPERATURE_DRAFT = 0.7

QUALITY_THRESHOLDS = {
    "coverage": 0.8,      # Minimum coverage of key topics
    "depth": 0.7,        # Minimum technical depth score
    "coherence": 0.75,   # Minimum coherence/flow score
    "citation": 0.9      # Minimum citation completeness
}

class ReportStyle(str, Enum):
    """Available report styles"""
    ACADEMIC = "academic"
    EXECUTIVE = "executive" 
    JOURNALISTIC = "journalistic"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"

class SourceReference(BaseModel):
    """Reference to a source used in the report"""
    source_id: str = Field(description="Unique identifier for the source")
    title: Optional[str] = Field(None, description="Title of the source")
    url: Optional[str] = Field(None, description="URL of the source if applicable")
    author: Optional[str] = Field(None, description="Author of the source")
    publication_date: Optional[str] = Field(None, description="Publication date of the source")
    snippet: Optional[str] = Field(None, description="Brief snippet from the source")

class SourceAgentQuery(BaseModel):
    """Query to a source agent for clarification"""
    agent_id: str = Field(description="ID of the source agent to query")
    question: str = Field(description="The question to ask the source agent")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")

class ReportSection(BaseModel):
    """A section of the generated report"""
    title: str = Field(description="Title of the section")
    content: str = Field(description="Content of the section")
    sources: List[SourceReference] = Field(description="Sources referenced in this section")

class ReportDraft(BaseModel):
    """A draft of the research report"""
    title: str = Field(description="Title of the report")
    summary: str = Field(description="Executive summary of the report")
    sections: List[ReportSection] = Field(description="Sections of the report")
    references: List[SourceReference] = Field(description="All references used in the report")
    keywords: List[str] = Field(description="Keywords relevant to the report")

class WriterRequest(BaseModel):
    """Request model for generating a report draft"""
    writing_context_id: str = Field(description="ID from the Router_04 writing context")
    refined_query: str = Field(description="The refined research query")
    context_summary: Dict[str, Any] = Field(description="Summary context from Router_04")
    source_agents: Dict[str, Any] = Field(description="Source agents and their assignments")
    reranked_sources: Dict[str, Any] = Field(description="Reranked and filtered sources")
    thematic_clusters: Dict[str, List[str]] = Field(description="Sources grouped by theme")
    report_style: ReportStyle = Field(description="Style of report to generate")
    user_background: Dict[str, Any] = Field(description="User background information")

class WriterResponse(BaseModel):
    """Response model for a report draft"""
    draft_id: str = Field(description="Unique identifier for this draft")
    report_draft: ReportDraft = Field(description="The generated report draft")
    suggested_improvements: List[str] = Field(description="Suggestions for improving the draft")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuing refinement")

class WriterFeedbackRequest(BaseModel):
    """Request model for providing feedback on a report draft"""
    draft_id: str = Field(description="ID of the draft to provide feedback on")
    feedback: str = Field(description="User feedback on the draft")
    conversation_id: str = Field(description="Conversation ID for the ongoing refinement")

class WriterFeedbackResponse(BaseModel):
    """Response model for feedback incorporation"""
    draft_id: str = Field(description="New draft ID")
    updated_draft: ReportDraft = Field(description="The updated report draft")
    changes_made: List[str] = Field(description="Summary of changes made based on feedback")
    is_complete: bool = Field(description="Whether the draft is considered complete")
    conversation_id: str = Field(description="Conversation ID for continuing refinement")

class QualityScore(BaseModel):
    """Quality assessment scores for a draft"""
    coverage: float = Field(description="Topic coverage score (0-1)")
    depth: float = Field(description="Technical depth score (0-1)")
    coherence: float = Field(description="Coherence and flow score (0-1)")
    citation: float = Field(description="Citation completeness score (0-1)")

class DraftEvaluation(BaseModel):
    """Evaluation results for a draft"""
    scores: QualityScore = Field(description="Quality scores")
    improvements_needed: List[str] = Field(description="Specific improvements needed")
    meets_threshold: bool = Field(description="Whether the draft meets quality thresholds")

class SourceAnalysis(BaseModel):
    """Analysis of a source's content and relevance"""
    key_information: List[Dict[str, Any]] = Field(description="Extracted key information")
    contradictions: List[Dict[str, Any]] = Field(description="Identified contradictions")
    clarification_needed: List[Dict[str, Any]] = Field(description="Questions needing clarification")
    connections: List[Dict[str, Any]] = Field(description="Thematic connections identified")

class SourceAgentMessage(TypedDict):
    """Message format for source agent communication"""
    agent_id: str
    content: str
    message_type: Literal["query", "response", "clarification"]
    context: Optional[Dict[str, Any]]

class SourceAgentConversation(BaseModel):
    """Tracks conversation with a source agent"""
    agent_id: str = Field(description="ID of the source agent")
    messages: List[SourceAgentMessage] = Field(default_factory=list, description="Conversation history")
    themes: List[str] = Field(default_factory=list, description="Themes this agent handles")
    source_types: List[str] = Field(default_factory=list, description="Types of sources this agent handles")

class WriterToSourceHandoff(BaseModel):
    """Data passed when writer hands off to a source agent"""
    query: str = Field(description="The clarification query")
    source_id: str = Field(description="ID of the source needing clarification") 
    context: Dict[str, Any] = Field(description="Additional context for the query")
    priority: int = Field(description="Query priority (1-5, 1 being highest)")

# Meta prompts for the Writer agent
WRITER_META_PROMPT = """
You are an expert research writer specializing in synthesizing complex information into clear, comprehensive reports. Your task is to create a high-quality research report based on the provided sources and user context.

# USER BACKGROUND
User Type: {user_type}
Research Purpose: {research_purpose}
Query Frequency: {query_frequency}

# RESEARCH CONTEXT
Refined Query: {refined_query}
Top Topics: {top_topics}
Writing Guidance: {writing_guidance}

# SOURCE INFORMATION
Available Sources: {source_count} sources across {source_types}
Thematic Organization: {thematic_clusters}
Source Quality Distribution: {quality_distribution}

# YOUR CAPABILITIES AND TOOLS
You have access to the following abilities to help you craft an optimal report:
1. Query sources directly to extract specific information
2. Request clarification from source agents when information is unclear or contradictory
3. Structure content according to thematic clusters or user-specified organization
4. Tailor technical depth based on user background and preferences
5. Organize information according to different structural approaches (chronological, thematic, etc.)

# YOUR RESPONSIBILITIES
1. Synthesize information from multiple high-quality sources into a coherent narrative
2. Maintain critical evaluation of source quality and reliability in your synthesis
3. Organize content logically according to identified themes and topics
4. Adapt technical depth and complexity to match user background
5. Ensure all claims are properly supported by cited sources
6. Provide balanced coverage of the topic without undue emphasis on any single source
7. Include well-structured sections with clear transitions between topics
8. Generate relevant and valuable insights based on source analysis

# REPORT STRUCTURE
Your report should include:
1. A clear title reflecting the refined query and main findings
2. An executive summary highlighting key insights and conclusions
3. Multiple well-organized sections addressing different aspects of the topic
4. Citations to specific sources throughout the report
5. A conclusion that synthesizes the findings
6. A reference list of all sources used

# PROCESS GUIDELINES
1. First, review the available sources and their thematic organization
2. Identify key topics and subtopics to cover based on source quality and relevance
3. Determine the most logical structure for the information
4. Query specific sources or agents as needed for detailed information
5. Synthesize information across sources, noting areas of consensus and disagreement
6. Draft sections that build toward comprehensive understanding
7. Ensure proper citation of sources throughout

Your goal is to produce a research report that is accurate, comprehensive, well-organized, and tailored to the user's needs and background.

# REPORT STYLE
Style Guidance: {report_style}

Response Format: Generate a complete report draft structured according to the ReportDraft model specification. Each section should include relevant source citations.
"""

EVALUATION_PROMPT = """
You are evaluating a research report draft for quality and completeness. Your task is to assess:

1. Topic Coverage (0-1):
   - Are all key topics from the research plan addressed?
   - Is the coverage balanced and thorough?

2. Technical Depth (0-1):
   - Does the analysis match the user's expertise level?
   - Are technical concepts explained appropriately?

3. Coherence & Flow (0-1):
   - Does the narrative flow logically?
   - Are sections well-connected?

4. Citation Completeness (0-1):
   - Are claims properly supported by sources?
   - Are high-quality sources utilized effectively?

Return a JSON object with scores and specific improvement needs:
{
    "scores": {
        "coverage": float,
        "depth": float,
        "coherence": float,
        "citation": float
    },
    "improvements_needed": [
        "specific improvement suggestion",
        ...
    ],
    "meets_threshold": bool
}
"""

SOURCE_EXPLORATION_PROMPT = """
You are analyzing source material to extract key information for a research report.

Source Context:
{source_context}

Current Knowledge Gaps:
{knowledge_gaps}

Your task is to:
1. Identify the most relevant information from this source
2. Note any contradictions with other sources
3. Flag areas needing clarification from source agents
4. Suggest connections to other topics/themes

Return a JSON object with your analysis:
{
    "key_information": [
        {"content": "extracted info", "relevance": float, "theme": "theme"}
    ],
    "contradictions": [
        {"content": "contradiction details", "source_ids": ["id1", "id2"]}
    ],
    "clarification_needed": [
        {"question": "specific question", "agent_id": "agent_id"}
    ],
    "connections": [
        {"from_theme": "current theme", "to_theme": "related theme", "relationship": "explanation"}
    ]
}
"""

class Writer:
    """Empowered writer agent with source agent coordination"""
    
    def __init__(self, model: str = WRITER_MODEL):
        self.client = OpenRouterClient()
        self.model = model
        self.max_tokens = MAX_TOKENS_DRAFT
        self.temperature = TEMPERATURE_DRAFT
        self.conversation_history = []
        self.context_summary = None
        self.source_agents = {}
        self.reranked_sources = {}
        self.thematic_clusters = {}
        self.user_background = {}
        self.draft_iterations = []
        self.source_analyses = {}
        self.agent_clarifications = {}
        self.knowledge_gaps = []
        self.agent_conversations: Dict[str, SourceAgentConversation] = {}
        self.reasoning_log: List[Dict[str, Any]] = []
        self.source_director = SourceDirector()
        self.source_agent_states: Dict[str, Dict[str, Any]] = {}
        self.pending_clarifications: List[WriterToSourceHandoff] = []

    def _generate_draft_id(self) -> str:
        """Generate a unique identifier for a report draft"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = os.urandom(4).hex()
        return f"draft_{timestamp}_{random_part}"
        
    def _init_system_prompt(
        self,
        context_summary: Dict[str, Any],
        source_agents: Dict[str, Any],
        report_style: ReportStyle,
        user_background: Dict[str, Any]
    ):
        """
        Initialize the system prompt with context from Router_04 and user background.
        
        Args:
            context_summary: Summary context from Router_04
            source_agents: Information on source agents and their assignments
            report_style: Style preference for the report
            user_background: User background information
        """
        # Extract relevant fields for the prompt
        refined_query = context_summary.get("refined_query", "")
        top_topics = context_summary.get("top_topics", [])
        writing_guidance = context_summary.get("writing_guidance", {})
        
        # Source metadata
        source_count = len(context_summary.get("sources", {}))
        source_types = context_summary.get("source_composition", {})
        thematic_clusters = context_summary.get("thematic_clusters", {})
        
        # Quality information for sources
        qualities = [s.get("quality_score", 0) for s in context_summary.get("sources", {}).values()]
        quality_distribution = {
            "high": sum(1 for q in qualities if q >= 0.8),
            "medium": sum(1 for q in qualities if 0.5 <= q < 0.8),
            "low": sum(1 for q in qualities if q < 0.5)
        }
        
        # User background information
        user_type = user_background.get("user_type", "Researcher")
        research_purpose = user_background.get("research_purpose", "Research")
        query_frequency = user_background.get("query_frequency", "occasional")
        
        # Format the meta prompt
        formatted_prompt = WRITER_META_PROMPT.format(
            user_type=user_type,
            research_purpose=research_purpose,
            query_frequency=query_frequency,
            refined_query=refined_query,
            top_topics=", ".join(top_topics[:5]),
            writing_guidance=json.dumps(writing_guidance, indent=2),
            source_count=source_count,
            source_types=", ".join([f"{k}: {v}" for k, v in source_types.items()]),
            thematic_clusters=len(thematic_clusters),
            quality_distribution=json.dumps(quality_distribution),
            report_style=report_style.value
        )
        
        # Clear existing history and set the formatted system prompt
        self.conversation_history = [
            {"role": "system", "content": formatted_prompt}
        ]
    
    async def _analyze_source(self, source_id: str, content: str) -> SourceAnalysis:
        """Analyze a source to extract key information and identify gaps"""
        prompt = SOURCE_EXPLORATION_PROMPT.format(
            source_context=content,
            knowledge_gaps=json.dumps(self.knowledge_gaps)
        )
        
        try:
            response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MAX_TOKENS_INTERNAL,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response["choices"][0]["message"]["content"])
            return SourceAnalysis(**analysis)
            
        except Exception as e:
            print(f"Error analyzing source {source_id}: {e}")
            return SourceAnalysis(
                key_information=[],
                contradictions=[],
                clarification_needed=[],
                connections=[]
            )
            
    async def _evaluate_draft(self, draft: ReportDraft) -> DraftEvaluation:
        """Evaluate a draft for quality and completeness"""
        eval_context = {
            "draft": draft.dict(),
            "user_background": self.user_background,
            "thematic_clusters": self.thematic_clusters
        }
        
        try:
            response = await self.client.chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": EVALUATION_PROMPT},
                    {"role": "user", "content": json.dumps(eval_context)}
                ],
                max_tokens=MAX_TOKENS_INTERNAL,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            evaluation = json.loads(response["choices"][0]["message"]["content"])
            return DraftEvaluation(**evaluation)
            
        except Exception as e:
            print(f"Error evaluating draft: {e}")
            return DraftEvaluation(
                scores=QualityScore(coverage=0, depth=0, coherence=0, citation=0),
                improvements_needed=["Error in evaluation"],
                meets_threshold=False
            )

    async def _explore_sources(self) -> None:
        """Autonomously explore sources and identify areas needing clarification"""
        analyses = await asyncio.gather(*[
            self._analyze_source(source_id, source.content)
            for source_id, source in self.reranked_sources.items()
        ])
        
        for source_id, analysis in zip(self.reranked_sources.keys(), analyses):
            self.source_analyses[source_id] = analysis
            
        for source_id, analysis in self.source_analyses.items():
            for clarification in analysis.clarification_needed:
                if clarification["agent_id"] not in self.agent_clarifications:
                    self.agent_clarifications[clarification["agent_id"]] = []
                self.agent_clarifications[clarification["agent_id"]].append({
                    "source_id": source_id,
                    "question": clarification["question"]
                })
                
        self.knowledge_gaps = [
            gap for analysis in analyses
            for gap in analysis.clarification_needed
        ]

    async def _coordinate_source_agents(self, clarification_requests: List[WriterToSourceHandoff]) -> None:
        """Coordinate multiple source agents for parallel clarifications"""
        
        # Group requests by source agent
        agent_requests: Dict[str, List[WriterToSourceHandoff]] = {}
        for request in clarification_requests:
            agent_id = next(
                (aid for aid, state in self.source_agent_states.items() 
                 if request.source_id in state.get("assigned_sources", [])),
                None
            )
            if agent_id:
                if agent_id not in agent_requests:
                    agent_requests[agent_id] = []
                agent_requests[agent_id].append(request)

        # Process requests in parallel
        async def process_agent_requests(agent_id: str, requests: List[WriterToSourceHandoff]):
            try:
                for request in sorted(requests, key=lambda r: r.priority):
                    clarification = await self.source_director.get_clarification({
                        "agent_id": agent_id,
                        "source_id": request.source_id,
                        "query": request.query,
                        "context": request.context
                    })
                    
                    # Store clarification result
                    if request.source_id not in self.source_analyses:
                        self.source_analyses[request.source_id] = {}
                    self.source_analyses[request.source_id][request.query] = clarification
                    
            except Exception as e:
                print(f"Error processing requests for agent {agent_id}: {e}")

        # Run all agent requests in parallel
        await asyncio.gather(*[
            process_agent_requests(agent_id, requests)
            for agent_id, requests in agent_requests.items()
        ])

    async def _get_agent_clarification(self, handoff: WriterToSourceHandoff) -> Optional[str]:
        """Get clarification from a specific source agent with proper handoff"""
        try:
            # Find the responsible agent
            agent_id = next(
                (aid for aid, state in self.source_agent_states.items() 
                 if handoff.source_id in state.get("assigned_sources", [])),
                None
            )
            
            if not agent_id:
                return None
                
            # Request clarification through director
            response = await self.source_director.get_clarification({
                "agent_id": agent_id,
                "source_id": handoff.source_id,
                "query": handoff.query,
                "context": handoff.context
            })
            
            return response.clarification if response else None
            
        except Exception as e:
            print(f"Error getting clarification: {e}")
            return None

    async def generate_draft(self, request: WriterRequest) -> WriterResponse:
        """Generate an optimal draft through autonomous exploration and iteration"""
        # Initialize with context
        self._init_system_prompt(
            request.context_summary,
            request.source_agents,
            request.report_style,
            request.user_background
        )
        
        # Store context and initialize source agent states
        self.context_summary = request.context_summary
        self.source_agents = request.source_agents
        self.reranked_sources = request.reranked_sources
        self.thematic_clusters = request.thematic_clusters
        self.user_background = request.user_background
        
        # Initialize source agent states from context
        self.source_agent_states = {
            agent_id: {
                "assigned_sources": info.get("assigned_sources", []),
                "themes": info.get("themes", []),
                "priority": info.get("priority", 99)
            }
            for agent_id, info in request.source_agents.items()
        }
        
        # Phase 1: Autonomous Source Exploration
        self._log_reasoning(
            "source_exploration",
            {"source_count": len(request.reranked_sources)},
            "Analyzing sources to extract key information and identify knowledge gaps"
        )
        await self._explore_sources()
        
        # Phase 2: Get Clarifications from Source Agents (updated with coordination)
        if self.knowledge_gaps:
            self._log_reasoning(
                "request_clarifications",
                {"gaps": self.knowledge_gaps},
                "Requesting coordinated clarifications from source agents"
            )
            
            # Convert knowledge gaps to handoff requests
            clarification_requests = []
            for gap in self.knowledge_gaps:
                if isinstance(gap, dict) and "agent_id" in gap and "question" in gap:
                    handoff = WriterToSourceHandoff(
                        query=gap["question"],
                        source_id=gap.get("source_id", "unknown"),
                        context={"gap_type": gap.get("type", "general")},
                        priority=gap.get("priority", 3)
                    )
                    clarification_requests.append(handoff)
            
            # Process all clarifications in parallel
            await self._coordinate_source_agents(clarification_requests)

        # Phase 3: Generate Initial Draft
        try:
            # Format the core writing prompt
            prompt = f"""Based on our exploration of the sources and gathered clarifications, 
            generate a comprehensive research report that addresses:

            1. Key findings from source analysis
            2. Integration of clarified points from source agents
            3. Thematic organization based on identified clusters
            4. Technical depth appropriate for the user's background

            Context Summary: {json.dumps(self.context_summary)}
            Source Analyses: {json.dumps(self.source_analyses)}
            Agent Clarifications: {json.dumps(self.agent_clarifications)}
            """

            # Get initial draft from LLM
            response = await self.client.chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.conversation_history[0]["content"]},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKENS_DRAFT,
                temperature=0.7
            )
            
            initial_content = response["choices"][0]["message"]["content"]
            current_draft = self._parse_draft_content(initial_content, self.context_summary.get("refined_query", ""))
            
        except Exception as e:
            print(f"Error generating initial draft: {e}")
            current_draft = ReportDraft(
                title=self.context_summary.get("refined_query", "Research Report"),
                summary="Error generating initial draft. Please try again.",
                sections=[],
                references=[],
                keywords=[]
            )
        
        # Phase 4: Autonomous Draft Iteration
        max_iterations = 5
        iteration = 0
        evaluation = None
        
        while iteration < max_iterations:
            evaluation = await self._evaluate_draft(current_draft)
            
            if evaluation.meets_threshold:
                break
                
            current_draft = await self._iterate_draft(current_draft)
            iteration += 1
            
        # Return the final draft with iteration history
        return WriterResponse(
            draft_id=self._generate_draft_id(),
            report_draft=current_draft,
            suggested_improvements=evaluation.improvements_needed if evaluation and not evaluation.meets_threshold else [],
            conversation_id=str(id(self.conversation_history))
        )

async def generate_draft(request: WriterRequest) -> WriterResponse:
    writer = Writer()
    response = await writer.generate_draft(request)
    await writer.client.client.aclose()
    return response

async def refine_draft(request: WriterFeedbackRequest) -> WriterFeedbackResponse:
    writer = Writer()
    response = await writer.refine_draft(request)
    await writer.client.client.aclose()
    return response