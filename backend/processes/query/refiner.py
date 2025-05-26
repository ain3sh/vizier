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
import asyncio, uuid
from typing import List, Dict, Optional, Tuple, Union
from backend.routers.openrouter import OpenRouterClient
from pydantic import BaseModel, Field
from fastapi import HTTPException


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
    conversation_id: Optional[str] = Field(None, description="ID for continuing an existing refinement conversation")  # Added conversation_id
class QueryResponse(BaseModel):
    """Response model for refined query"""
    refined_query: str = Field(description="The refined query")
    is_complete: bool = Field(description="Whether the refinement process is complete")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuing the refinement")
    input_tokens: Optional[int] = Field(None, description="Number of input tokens used for the refinement (native count)")
    output_tokens: Optional[int] = Field(None, description="Number of output tokens generated for the refinement (native count)")
    cost: Optional[float] = Field(None, description="Cost of the refinement API call in USD")


# Global store for active refiner instances (simple in-memory approach)
# Warning: This won't scale across multiple server processes and instances might leak memory if not cleaned up.
active_refiners: Dict[str, "QueryRefiner"] = {}


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
            max_tokens: Max tokens for the LLM response.
            temperature: Sampling temperature for the LLM.
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
            background.query_frequency,
            self.max_tokens
        )


    async def refine_query(self, current_query: str) -> Optional[Tuple[str, Dict[str, Union[int, float]]]]:
        """
        Performs one round of query refinement using the LLM.
        Also retrieves and returns the cost and token usage details for the API call.

        Args:
            current_query: The user's latest query or feedback.

        Returns:
            The refined query suggested by the LLM, or None if an error occurs.
        """
        cost_info = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}
        refined_query_content = None

        # add user's latest input to conversation history
        self.conversation_history.append({"role": "user", "content": current_query})

        try: # get refined query from LLM
            response = await self.client.chat_completion(
                model=self.model,
                messages=self.conversation_history,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            # extract content and generation ID based on OpenRouter formatting
            if isinstance(response, dict) and 'choices' in response:
                if len(response['choices']) > 0 and 'message' in response['choices'][0]:
                    refined_query_content = response['choices'][0]['message']['content']
                    generation_id = response.get('id')

                    if generation_id:
                        await asyncio.sleep(2) # wait for details to be available
                        try:
                            details = await self.client.get_generation_details(generation_id)
                            stats = details.get('data', {})
                            # Store native token counts and total cost
                            cost_info["input_tokens"] = stats.get('native_tokens_prompt', 0)
                            cost_info["output_tokens"] = stats.get('native_tokens_completion', 0)
                            cost_info["cost"] = stats.get('total_cost', 0.0)
                        except Exception as detail_error:
                            print(f"Warning: Could not retrieve generation details for {generation_id}: {detail_error}")
                    else:
                        print("Warning: No generation ID found in response, cannot retrieve cost details.")

                    # add the assistant's response to the history *after* potential detail retrieval
                    self.conversation_history.append({"role": "assistant", "content": refined_query_content})
                    return refined_query_content, cost_info
                else:
                    print(f"Unexpected response structure: 'message' not found in choices[0]. Response: {response}")
            else:
                print(f"Unexpected response format: {response}")
                return None

        except Exception as e:
            print(f"Error during LLM call: {e}")
            # remove the user message that caused the error to avoid infinite loops
            if len(self.conversation_history) > 1 and self.conversation_history[-1]['role'] == 'user':
                self.conversation_history.pop()
            return None

    async def process_query(self, query: str, background: UserBackground) -> Optional[QueryResponse]:
        """
        Process the *initial* query for API integration. Sets background and performs first refinement.

        Args:
            query: User's initial query
            background: User background information

        Returns:
            QueryResponse with the first refined query and completion status
        """
        # Set up user background - this initializes the conversation history
        self.set_user_background(background)

        # get the refined query and cost info from the LLM for the first time
        refinement_result = await self.refine_query(query)

        if refinement_result is None:
            # Return a response indicating failure but keep is_complete=False
            return QueryResponse(
                refined_query="Unable to process initial query. Please try again.",
                is_complete=False,
                input_tokens=0,
                output_tokens=0,
                cost=0.0
            )

        refined_query, cost_info = refinement_result

        return QueryResponse(
            refined_query=refined_query,
            is_complete=False, # First step is never complete
            conversation_id=None, # ID will be added by the endpoint
            **cost_info # unpack input_tokens, output_tokens, cost
        )

    async def continue_refinement(self, feedback: str) -> Optional[QueryResponse]:
        """
        Process user feedback for an ongoing refinement conversation.

        Args:
            feedback: User's feedback on the previous refinement.

        Returns:
            QueryResponse with the newly refined query.
        """
        # History is already established, just add feedback and get next refinement
        refinement_result = await self.refine_query(feedback)

        if refinement_result is None:
            # Return a response indicating failure
             return QueryResponse(
                refined_query="Unable to process feedback. Please try again.",
                is_complete=False, # Keep refinement going if possible
                input_tokens=0,
                output_tokens=0,
                cost=0.0
            )

        refined_query, cost_info = refinement_result

        return QueryResponse(
            refined_query=refined_query,
            is_complete=False, # API assumes one refinement per call
            conversation_id=None, # ID will be added by the endpoint
            **cost_info # unpack input_tokens, output_tokens, cost
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
        # Set up background info using the existing method
        self.set_user_background(background)

        current_input = initial_query
        approved_query = None

        while True:
            print(f"\nRefining query: '{current_input[:100]}...'")
            refined_query = await self.refine_query(current_input)

            if refined_query is None:
                print("Failed to get refinement from the model. Please try again or modify your input.")
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
                    print("Exiting refinement loop due to unrecoverable error.")
                    return initial_query

            # unpack the result
            refined_query_content, cost_info = refined_query

            print("\n---------------- Refined Query Suggestion ----------------")
            print(refined_query_content)
            print(f"(Tokens: In={cost_info['input_tokens']}, Out={cost_info['output_tokens']} | Cost: ${cost_info['cost']:.6f})")
            print("--------------------------------------------------------")

            feedback = input("Is this refined query good? (y/n/provide feedback): ").strip()
            if feedback.lower() == 'y':
                approved_query = refined_query_content
                print("\nQuery Approved!")
                break
            elif feedback.lower() == 'n':
                current_input = input("Please provide feedback or a new version of the query: ").strip()
                if not current_input:  # handle empty input
                    print("No feedback provided. Re-using the last suggestion for refinement.")
                    current_input = refined_query_content # Use the content for re-refinement
                    # remove the last assistant message to avoid confusion
                    if self.conversation_history[-1]['role'] == 'assistant':
                        self.conversation_history.pop()
            else:
                # user provided specific feedback directly
                current_input = feedback

        await self.client.client.aclose() # close client connection
        return approved_query if approved_query else initial_query



#? FastAPI interface for query refinement
async def refine_query(request: QueryRequest,
                       model: str,
                       max_output_tokens: int = 1000,
                       temperature: float = 0.6
                       ) -> QueryResponse:
    """
    API endpoint for refining a user query, supporting iterative refinement.

    If `conversation_id` is provided and valid, it continues an existing refinement.
    Otherwise, it starts a new refinement session.

    Args:
        request: The query request containing the user query/feedback, background info, and optional conversation_id.
        model: The model to use for refinement.
        max_output_tokens: Maximum tokens for the model output.
        temperature: Sampling temperature for the model.

    Returns:
        QueryResponse with the refined query content, token usage, cost information, and conversation_id.
    """
    conversation_id = request.conversation_id
    refiner: Optional[QueryRefiner] = None
    response: Optional[QueryResponse] = None

    if conversation_id and conversation_id in active_refiners:
        # Continue existing conversation
        print(f"Continuing conversation: {conversation_id}")
        refiner = active_refiners[conversation_id]
        response = await refiner.continue_refinement(request.query)
        if response:
            response.conversation_id = conversation_id  # Ensure ID is returned
    else:
        # Start new conversation
        print("Starting new conversation")
        refiner = QueryRefiner(model=model, max_tokens=max_output_tokens, temperature=temperature)
        conversation_id = str(uuid.uuid4())  # Generate new ID
        active_refiners[conversation_id] = refiner  # Store the new refiner instance
        print(f"New conversation ID: {conversation_id}")
        response = await refiner.process_query(request.query, request.background)
        if response:
            response.conversation_id = conversation_id  # Add the new ID to the response

    if response is None:
        if conversation_id and conversation_id in active_refiners:
            # Clean up failed refiner instance if it was just added
            if refiner == active_refiners.get(conversation_id):  # Check if it's the one we just added
                del active_refiners[conversation_id]
        raise HTTPException(status_code=500, detail="Failed to process query refinement.")

    return response




async def test_chat_completion(): #! FOR TESTING ONLY
    """
    Basic test function to verify OpenRouter API connectivity.
    """
    client = OpenRouterClient()
    try:
        print("Testing OpenRouter API connection...")
        response = await client.chat_completion(
            model="google/gemma-3-27b-it:free",
            messages=[
                {
                    "role": "user",
                    "content": "What's the capital of France?"
                }
            ],
            max_tokens=10,
            temperature=0.7
        )
        print("Test Response:\n", response)

        # Extract assistant message and generation ID
        assistant_message = response.get('choices', [{}])[0].get('message', {}).get('content')
        generation_id = response.get('id')

        if assistant_message:
            print("Assistant message:\n", assistant_message)
        else:
            print("Could not extract assistant message.")

        if generation_id:
            print(f"Generation ID: {generation_id}")
            await asyncio.sleep(2) # Wait for details
            details = await client.get_generation_details(generation_id)
            print("Generation Details:\n", details)
            print("Connection and detail retrieval successful!")
        else:
            print("Warning: Could not retrieve generation ID from test response.")
        return True
    except Exception as e:
        print(f"Test connection failed: {e}")
        return False
    finally:
        await client.client.aclose()  # close AsyncClient


async def main(): #! FOR CLI TESTING ONLY
    """
    Main function to run the command-line query refinement tool.
    Updated to mimic the stateful API flow using conversation IDs.
    """
    print("Starting Query Refinement Process...")

    # test connection first
    connection_ok = await test_chat_completion()
    if not connection_ok:
        print("Could not connect to OpenRouter API. Please check your API key and connection.")
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

    # --- Mimic API Flow ---
    current_conversation_id: Optional[str] = None
    current_query_input = initial_query
    final_query_content = None
    final_cost_info = {}
    is_complete = False
    refiner_instance: Optional[QueryRefiner] = None  # Keep track of the instance for cleanup

    while not is_complete:
        print(f"\nRefining query/feedback: '{current_query_input[:100]}...'")

        # Simulate API request object
        req = QueryRequest(query=current_query_input, background=background, conversation_id=current_conversation_id)

        # Simulate calling the API endpoint logic directly
        temp_conversation_id = req.conversation_id
        response: Optional[QueryResponse] = None

        if temp_conversation_id and temp_conversation_id in active_refiners:
            # Continue existing conversation
            refiner_instance = active_refiners[temp_conversation_id]
            response = await refiner_instance.continue_refinement(req.query)
            if response:
                response.conversation_id = temp_conversation_id
        else:
            # Start new conversation
            refiner_instance = QueryRefiner(
                model="google/gemma-3-27b-it:free",  # Or get from user input
                max_tokens=1000,
                temperature=0.6
            )
            temp_conversation_id = str(uuid.uuid4())
            active_refiners[temp_conversation_id] = refiner_instance
            response = await refiner_instance.process_query(req.query, req.background)
            if response:
                response.conversation_id = temp_conversation_id
                current_conversation_id = temp_conversation_id  # Store the ID for next iteration

        # --- End Simulate API call ---

        if response is None or not response.refined_query or "Unable to process" in response.refined_query:
            print(f"Failed to get refinement: {response.refined_query if response else 'No response'}")
            # Decide whether to break or allow retry
            retry = input("Retry with new input? (y/n): ").lower()
            if retry != 'y':
                print("Exiting refinement loop due to error.")
                break
            else:
                current_query_input = input("Please provide new feedback or query: ").strip()
                if not current_query_input:
                    print("Input cannot be empty. Exiting.")
                    break
                continue  # Skip to next iteration with new input

        final_query_content = response.refined_query  # Store latest refinement
        final_cost_info = {  # Store latest cost info
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost": response.cost
        }
        # Update conversation ID if it was newly created
        if response.conversation_id:
            current_conversation_id = response.conversation_id

        print("\n---------------- Refined Query Suggestion ----------------")
        print(final_query_content)
        print(f"(Tokens: In={final_cost_info.get('input_tokens', 0)}, Out={final_cost_info.get('output_tokens', 0)} | Cost: ${final_cost_info.get('cost', 0.0):.6f})")
        print(f"(Conversation ID: {current_conversation_id})")  # Show the ID
        print("--------------------------------------------------------")

        feedback = input("Is this refined query good? (y/n/provide feedback): ").strip()

        if feedback.lower() == 'y':
            print("\nQuery Approved!")
            is_complete = True
        elif feedback.lower() == 'n':
            current_query_input = input("Please provide feedback or a new version of the query: ").strip()
            if not current_query_input:
                print("No feedback provided. Re-using the last suggestion for refinement.")
                current_query_input = final_query_content  # Use the content for re-refinement
        else:
            # User provided specific feedback directly
            current_query_input = feedback

    # Display final approved query if refinement completed successfully
    if is_complete and final_query_content:
        print("\n================ Final Approved Query ================")
        print(final_query_content)
        print(f"(Final Tokens: In={final_cost_info.get('input_tokens', 0)}, Out={final_cost_info.get('output_tokens', 0)} | Final Cost: ${final_cost_info.get('cost', 0.0):.6f})")
        print("====================================================")
        print("\nThis refined query is now ready to guide a comprehensive research process.")
    elif not final_query_content:
        print("\nRefinement process did not complete successfully.")

    # Clean up the refiner instance used in the loop
    if current_conversation_id and current_conversation_id in active_refiners:
        print(f"\nCleaning up conversation: {current_conversation_id}")
        refiner_to_close = active_refiners.pop(current_conversation_id)
        await refiner_to_close.client.client.aclose()
    elif refiner_instance:  # Handle case where loop exited before ID was stored but instance exists
        await refiner_instance.client.client.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())  # Run the main CLI testing function
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
``` 