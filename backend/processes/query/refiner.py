"""
Query Refiner Module

This module implements the query refinement process for Vizier. It transforms raw user queries
into refined, structured research plans through an iterative LLM-guided refinement loop.

The process follows this flow:
1. User submits an initial query
2. Meta-prompt guides an LLM to generate a refined query candidate
3. User provides feedback on the refined query
4. LLM incorporates feedback to produce an improved query
5. Loop continues until user approves the refined query
6. Final approved query is returned for downstream research planning

This component is the first stage in Vizier's research workflow, ensuring high-quality
inputs for subsequent data collection, analysis, and report generation stages.
"""

import asyncio
from typing import List, Dict, Optional
from routers.openrouter import OpenRouterClient
from pydantic import BaseModel, Field

# constants
REFINER_MODEL = "openrouter/optimus-alpha"
MAX_TOKENS_REFINEMENT = 500
TEMPERATURE_REFINEMENT = 0.7

META_PROMPT = """
You are an expert research assistant AI for specialized professionals and researchers. Your task is to transform user queries into comprehensive, actionable research plans that prioritize technical accuracy, timeliness, and depth.

**User Background Information:**
- User Type: {user_type}
- Research Purpose: {research_purpose}
- User Description: {user_description}
- Query Frequency: {query_frequency}

**Goal:** Transform the user's query, which may be vague or incomplete, into a structured research plan that identifies:
1. Precise sub-topics requiring investigation
2. Specific types of sources to prioritize (e.g., academic papers, preprints, technical blogs, expert social media)
3. Key experts, institutions, or research groups to focus on
4. Temporal considerations (recent developments vs. foundational knowledge)
5. Technical depth requirements appropriate for specialized professionals

**Input:** The user will provide their current query or feedback on your previous refinement attempt. This will be the last message in the conversation history.

**Output:** Generate a single, improved version of the research query as a structured plan. You MUST return the FULL COMPLETE refined query after each iteration, not just the parts affected by feedback. Be concise but comprehensive, with clear separation between different components of the research. Focus on technical precision, avoiding oversimplification.

**Example Interaction:**

*   **User:** "Update me on CRISPR developments"
*   **You (Refined Query):**
    "Research Plan: Investigate recent technical developments in CRISPR gene-editing technology with emphasis on specialized research applications.

    Key Research Components:
    1. Latest advances in CRISPR-Cas9 and alternative systems (Cas12, Cas13) within the past 6-12 months, focusing on enhanced precision, reduced off-target effects, and delivery mechanisms.
    2. Recent (2023-present) peer-reviewed publications and preprints from leading institutions (Broad Institute, Zhang Lab, Doudna Lab, Qi Lab).
    3. Technical breakthroughs in specific application domains: therapeutic applications for genetic disorders, agricultural applications, and diagnostic tools.
    4. Regulatory and ethical developments affecting research applications, particularly recent FDA/EMA decisions.
    5. Commercial and translational progress from key biotechnology companies (Editas, CRISPR Therapeutics, Intellia, Caribou).

    Sources to prioritize: Recent journal publications in Nature Biotechnology, Cell, Science; bioRxiv/medRxiv preprints; NIH/FDA announcements; technical content from specialized conferences."

*   **User:** "Focus more on base editing applications in particular."
*   **You (Further Refined Query):**
    "Refined Research Plan: Investigate recent technical developments in base editing applications of CRISPR technology.

    Key Research Components:
    1. Technical advances in cytosine and adenine base editor (CBE/ABE) systems within the past 12 months, with particular focus on expanded targeting scope, enhanced specificity, and reduced off-target effects.
    2. Comparative analysis of latest generation base editors (BE4max, ABE8e, etc.) versus prime editing for precise genetic modifications.
    3. Recent breakthrough applications in therapeutic contexts: 
       a. Base editing approaches for monogenic disorders (β-thalassemia, sickle cell disease, familial hypercholesterolemia)
       b. Cancer immunotherapy applications (PD-1, TCR modifications)
       c. In vivo delivery systems optimized for base editors (LNPs, AAVs, novel vectors)
    4. Key technical limitations and engineering solutions from Liu Lab (Broad Institute), Komor Lab (UCSD), and other leading research groups.
    5. Technological convergence of base editing with other precision gene modification approaches.

    Sources to prioritize: Nature Biotechnology publications since 2023; bioRxiv preprints; scientific proceedings from American Society of Gene & Cell Therapy; recent patents; NIH CRISPR clinical trial registrations; technical publications from Beam Therapeutics and Verve Therapeutics."

**Current Task:** Based on the entire conversation history, refine the latest user input into a better research query/plan. Remember to always return the FULL COMPLETE refined query, not just address the specific feedback points. Ensure your response is structured clearly with explicit research components, specific technical details to investigate, and prioritized information sources appropriate for specialized professionals.

**Response Max Tokens:** {max_tokens}
"""


# pydantic models for API requests/responses
class UserBackground(BaseModel):
    """User background information for query refinement"""
    user_type: str = Field(description="Type of user (e.g., 'Specialized Professional')")
    research_purpose: str = Field(description="What the user will use Vizier for")
    user_description: str = Field(description="Brief description of who the user is")
    query_frequency: str = Field(description="How often the query will be run (daily/weekly/monthly)")
class QueryRequest(BaseModel):
    """Request model for query refinement"""
    query: str = Field(description="The user's query or feedback on previous refinement")
    background: UserBackground = Field(description="User background information")
class QueryResponse(BaseModel):
    """Response model for refined query"""
    refined_query: str = Field(description="The refined query")
    is_complete: bool = Field(description="Whether the refinement process is complete")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuing the refinement")


class QueryRefiner:
    """
    Manages the iterative process of refining a user's research query using an LLM.
    """
    def __init__(self, model: str = REFINER_MODEL,
                    max_tokens: int = MAX_TOKENS_REFINEMENT,
                    temperature: float = TEMPERATURE_REFINEMENT):
        """
        Initializes the QueryRefiner.

        Args:
            model: The identifier of the language model to use for refinement.
        """
        self.client = OpenRouterClient()
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.conversation_history: List[Dict[str, str]] = []
        self._init_system_prompt(None, None, None, None, max_tokens)

    def _init_system_prompt(self, user_type: Optional[str], research_purpose: Optional[str],
                            user_description: Optional[str], query_frequency: Optional[str],
                            max_tokens: str):
        """Initialize the system prompt with user background information"""
        formatted_prompt = META_PROMPT.format(
            user_type=user_type or "Unknown",
            research_purpose=research_purpose or "Unknown",
            user_description=user_description or "Unknown",
            query_frequency=query_frequency or "Unknown",
            max_tokens=max_tokens
        )

        # clear existing history and set the formatted system prompt
        self.conversation_history = [
            {"role": "system", "content": formatted_prompt}
        ]

    def set_user_background(self, background: UserBackground):
        """
        Set user background information for the refiner.

        Args:
            background: UserBackground object with user information
        """
        self._init_system_prompt(
            background.user_type,
            background.research_purpose,
            background.user_description,
            background.query_frequency
        )


    async def refine_query(self, current_query: str) -> Optional[str]:
        """
        Performs one round of query refinement using the LLM.

        Args:
            current_query: The user's latest query or feedback.

        Returns:
            The refined query suggested by the LLM, or None if an error occurs.
        """
        # add user's latest input to conversation history
        self.conversation_history.append({"role": "user", "content": current_query})

        try: # get refined query from LLM
            response = await self.client.chat_completion(
                model=self.model,
                messages=self.conversation_history,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            # extract content based on OpenRouter formatting
            if isinstance(response, dict) and 'choices' in response:
                if len(response['choices']) > 0 and 'message' in response['choices'][0]:
                    refined_query = response['choices'][0]['message']['content']

                    # add the assistant's response to conversation history
                    self.conversation_history.append({"role": "assistant", "content": refined_query})
                    return refined_query.strip()

                else:
                    print("Unexpected response format - no message in choice")
                    print(f"Response data: {response}")
                    return None
            else:
                print(f"Unexpected response format: {response}")
                return None

        except Exception as e:
            print(f"Error during LLM call: {e}")
            # remove the user message that caused the error to avoid infinite loops
            if len(self.conversation_history) > 1 and self.conversation_history[-1]['role'] == 'user':
                self.conversation_history.pop()
            return None

    async def process_query(self, query: str, background: UserBackground) -> QueryResponse:
        """
        Process a new query or feedback for API integration.

        Args:
            query: User's query or feedback
            background: User background information

        Returns:
            QueryResponse with refined query and completion status
        """
        # Set up user background if this is a new conversation or background changed
        self.set_user_background(background)

        # get the refined query from the LLM
        refined_query = await self.refine_query(query)
        if refined_query is None:
            return QueryResponse(
                refined_query="Unable to process query. Please try again with a different query.",
                is_complete=False
            )

        #? since API: assume one refinement at a time, so is_complete is always False
            # frontend needs to send a new request with feedback or approval
        return QueryResponse(
            refined_query=refined_query,
            is_complete=False,
            conversation_id=str(id(self.conversation_history))  # Simple unique ID
        )

    async def finalize_query(self, conversation_id: str) -> QueryResponse:
        """
        Mark the current query as approved.

        Args:
            conversation_id: The conversation ID to finalize

        Returns:
            QueryResponse with the final query and completion status set to True
        """
        if not self.conversation_history or len(self.conversation_history) < 2:
            return QueryResponse(
                refined_query="No query has been processed yet.",
                is_complete=False
            )

        # get the last assistant message as the final query
        for message in reversed(self.conversation_history):
            if message["role"] == "assistant":
                return QueryResponse(
                    refined_query=message["content"],
                    is_complete=True,
                    conversation_id=conversation_id
                )

        return QueryResponse(
            refined_query="No refined query found in conversation history.",
            is_complete=False
        )


    #! FOR TESTING ONLY
    async def run_refinement_loop(self, initial_query: str, background: UserBackground) -> str:
        """
        Runs the interactive query refinement loop until the user approves.
        Used for CLI testing ONLY!

        Args:
            initial_query: The user's starting query.
            background: User background information.

        Returns:
            The final, user-approved refined query.
        """
        # Set up background info
        self.set_user_background(
            background.user_type,
            background.research_purpose,
            background.user_description,
            background.query_frequency
        )
        
        current_input = initial_query
        approved_query = None

        while True:
            print("\n⏳ Refining query...")
            refined_query = await self.refine_query(current_input)

            if refined_query is None:
                print("❌ Failed to get refinement from the model. Please try again or modify your input.")
                # get the last valid input as fallback
                if len(self.conversation_history) > 1:
                    last_valid_input = current_input  # Use current input as fallback
                    print(f"Last valid input was: '{last_valid_input[:100]}...'")

                    # ask user what to do
                    retry = input("Retry using the last valid input? (y/n): ").lower()
                    if retry != 'y':
                        print("Exiting refinement loop due to error.")
                        return current_input

                    # try again with same input
                    continue
                else:
                    return initial_query

            print("\n---------------- Refined Query Suggestion ----------------")
            print(refined_query)
            print("--------------------------------------------------------")

            feedback = input("Is this refined query good? (y/n/provide feedback): ").strip()
            if feedback.lower() == 'y':
                approved_query = refined_query
                print("\n✅ Query Approved!")
                break
            elif feedback.lower() == 'n':
                current_input = input("Please provide feedback or a new version of the query: ").strip()
                if not current_input:  # handle empty input
                    print("No feedback provided. Re-using the last suggestion for refinement.")
                    current_input = refined_query
                    # remove the last assistant message to avoid confusion
                    if self.conversation_history[-1]['role'] == 'assistant':
                        self.conversation_history.pop()
            else:
                # user provided specific feedback directly
                current_input = feedback

        await self.client.client.aclose() # close client connection
        return approved_query if approved_query else initial_query



#? FastAPI interface for query refinement
async def refine_query(request: QueryRequest) -> QueryResponse:
    """
    API endpoint for refining a user query.

    Args:
        request: The query request containing the user query and background info

    Returns:
        QueryResponse with the refined query
    """
    refiner = QueryRefiner()
    response = await refiner.process_query(request.query, request.background)
    await refiner.client.client.aclose()
    return response

async def approve_query(conversation_id: str) -> QueryResponse: #! OPTIONAL
    """
    API endpoint for approving the current refined query.

    Args:
        conversation_id: The ID of the conversation to finalize

    Returns:
        QueryResponse with the final approved query
    """
    refiner = QueryRefiner()
    response = await refiner.finalize_query(conversation_id)
    await refiner.client.client.aclose()
    return response




async def test_chat_completion(): #! FOR TESTING ONLY
    """
    Basic test function to verify OpenRouter API connectivity.
    """
    client = OpenRouterClient()
    try:
        print("Testing OpenRouter API connection...")
        response = await client.chat_completion(
            model=REFINER_MODEL,  # Using the same model as the refiner
            messages=[
                {
                    "role": "user",
                    "content": "What's the capital of France?"
                }
            ],
            max_tokens=50,
            temperature=0.7
        )
        print("Test Response:\n", response)
        print("Connection successful!")
        return True
    except Exception as e:
        print(f"Test connection failed: {e}")
        return False
    finally:
        await client.client.aclose()  # close AsyncClient


async def main(): #! FOR CLI TESTING ONLY
    """
    Main function to run the command-line query refinement tool.
    This provides a CLI testing interface that uses the same code
    as the API but with interactive prompts.
    """
    print("🚀 Starting Query Refinement Process...")

    # test connection first
    connection_ok = await test_chat_completion()
    if not connection_ok:
        print("⚠️ Could not connect to OpenRouter API. Please check your API key and connection.")
        return

    # collect user background information
    print("\nPlease provide some background information:")
    user_type = input("User Type (e.g., 'Specialized Professional'): ").strip() or "Specialized Professional"
    research_purpose = input("What will you be using Vizier for? (200 chars max): ").strip()[:200] or "Research"
    user_description = input("Who are you? (200 chars max): ").strip()[:200] or "Researcher"

    print("\nHow frequently will you run this query?")
    print("1) Daily")
    print("2) Weekly")
    print("3) Monthly")
    frequency_choice = input("Enter number (1-3): ").strip()
    query_frequency = {
        "1": "daily",
        "2": "weekly",
        "3": "monthly"
    }.get(frequency_choice, "weekly")

    # package background info
    background = UserBackground(
        user_type=user_type,
        research_purpose=research_purpose,
        user_description=user_description,
        query_frequency=query_frequency
    )

    # get initial query
    initial_query = ""
    while not initial_query:
        print("\nTell me what you'd like to research:")
        initial_query = input("Please enter your initial research query: ").strip()
        if not initial_query:
            print("Query cannot be empty. Please try again.")

    # use the API-compatible methods for consistency
    refiner = QueryRefiner()

    # initial refinement
    response = await refiner.process_query(initial_query, background)
    final_query = response.refined_query

    # feedback-based refinement loop
    while not response.is_complete:
        print("\n---------------- Refined Query Suggestion ----------------")
        print(final_query)
        print("--------------------------------------------------------")

        feedback = input("Is this refined query good? (y/n/provide feedback): ").strip()

        if feedback.lower() == 'y':
            response = await refiner.finalize_query(response.conversation_id or "")
            break

        else: # use the feedback (or ask for it if just 'n')
            if feedback.lower() == 'n':
                feedback = input("Please provide feedback for improvement: ").strip()
                if not feedback:
                    print("No feedback provided, using previous suggestion")
                    continue

            # process the feedback and get a new refined query
            print("⏳ Refining query based on feedback...")
            response = await refiner.process_query(feedback, background)
            final_query = response.refined_query

    # display final approved query
    print("\n================ Final Approved Query ================")
    print(final_query)
    print("====================================================")
    print("\nThis refined query is now ready to guide a comprehensive research process.")

    await refiner.client.client.aclose() # close client connection

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting query refinement process.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()