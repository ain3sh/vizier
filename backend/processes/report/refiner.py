"""
Draft Refiner Module

This module implements the draft refinement process for Vizier. It transforms initial report drafts
into polished, publication-ready documents through an iterative LLM-guided refinement loop.

The process follows this flow:
1. Initial draft is submitted
2. Meta-prompt guides an LLM to analyze and improve the draft
3. User provides feedback on the refined draft
4. LLM incorporates feedback to produce an improved version
5. Loop continues until user approves the final draft
6. Final approved draft is returned for formatting and export

This component helps ensure high-quality research report outputs by providing
systematic improvements to structure, clarity, and technical accuracy.
"""

import asyncio
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from routers.openrouter import OpenRouterClient

# Constants
REFINER_MODEL = "openrouter/optimus-alpha"
MAX_TOKENS_REFINEMENT = 2000  # Higher than query refiner since handling full drafts
TEMPERATURE_REFINEMENT = 0.7

META_PROMPT = """
You are an expert research report editor focusing on technical and academic writing. Your task is to refine research report drafts through iterative improvements, maintaining high standards for clarity, structure, and technical accuracy.

**Draft Context:**
- Report Type: {report_type}
- Technical Level: {technical_level}
- Target Audience: {target_audience}
- Length Guidelines: {length_guidelines}

**Goal:** Refine the draft while focusing on:
1. Technical accuracy and precision
2. Logical flow and structure
3. Clear presentation of research findings
4. Proper integration of sources and citations
5. Balanced coverage of topics
6. Professional academic tone
7. Adherence to style guidelines

**Input:** The user will provide either an initial draft or feedback on your previous refinement. This will be the last message in the conversation history.

**Output:** Generate a single, improved version of the draft. You MUST return the COMPLETE refined draft after each iteration, not just edited sections. Focus on substantive improvements while preserving the core research content.

**Refinement Priorities:**
1. Structural Coherence:
   - Clear section transitions
   - Balanced section lengths
   - Strong topic sentences
   - Effective use of subheadings

2. Technical Content:
   - Precise technical terminology
   - Clear explanation of complex concepts
   - Proper citation of technical claims
   - Accurate representation of research findings

3. Academic Standards:
   - Formal academic tone
   - Proper citation format
   - Clear methodology description
   - Objective presentation of findings

4. Readability:
   - Clear sentence structure
   - Professional vocabulary
   - Consistent terminology
   - Effective use of technical figures/tables references

**Current Task:** Based on the conversation history, analyze the latest draft or feedback and provide a refined version. Always return the COMPLETE refined draft with all sections. Ensure your refinements maintain technical accuracy while improving clarity and structure.

**Response Max Tokens:** {max_tokens}
"""

class ReportContext(BaseModel):
    """Context information for report refinement"""
    report_type: str = Field(description="Type of report (e.g., 'Research Paper', 'Technical Report')")
    technical_level: str = Field(description="Technical depth level (e.g., 'Expert', 'Intermediate')")
    target_audience: str = Field(description="Intended audience for the report")
    length_guidelines: str = Field(description="Target length and format guidelines")

class DraftRequest(BaseModel):
    """Request model for draft refinement"""
    draft_content: str = Field(description="The current draft content or feedback")
    context: ReportContext = Field(description="Report context information")

class DraftResponse(BaseModel):
    """Response model for refined draft"""
    refined_draft: str = Field(description="The refined draft content")
    suggested_improvements: List[str] = Field(default_factory=list, description="List of suggested further improvements")
    is_complete: bool = Field(description="Whether the refinement process is complete")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuing the refinement")

class DraftRefiner:
    """
    Manages the iterative process of refining research report drafts using an LLM.
    """
    def __init__(self, model: str = REFINER_MODEL,
                 max_tokens: int = MAX_TOKENS_REFINEMENT,
                 temperature: float = TEMPERATURE_REFINEMENT):
        """
        Initialize the DraftRefiner.

        Args:
            model: The identifier of the language model to use for refinement
            max_tokens: Maximum tokens for model response
            temperature: Temperature setting for generation
        """
        self.client = OpenRouterClient()
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.conversation_history: List[Dict[str, str]] = []
        self._init_system_prompt(None, None, None, None, max_tokens)

    def _init_system_prompt(self, report_type: Optional[str], technical_level: Optional[str],
                          target_audience: Optional[str], length_guidelines: Optional[str],
                          max_tokens: int):
        """Initialize the system prompt with report context information"""
        formatted_prompt = META_PROMPT.format(
            report_type=report_type or "Research Report",
            technical_level=technical_level or "Advanced",
            target_audience=target_audience or "Technical Professionals",
            length_guidelines=length_guidelines or "Standard research paper length",
            max_tokens=max_tokens
        )
        
        # Clear existing history and set the formatted system prompt
        self.conversation_history = [
            {"role": "system", "content": formatted_prompt}
        ]

    def set_report_context(self, context: ReportContext):
        """
        Set report context information for the refiner.

        Args:
            context: ReportContext object with report parameters
        """
        self._init_system_prompt(
            context.report_type,
            context.technical_level,
            context.target_audience,
            context.length_guidelines,
            self.max_tokens
        )

    async def refine_draft(self, current_draft: str) -> Optional[str]:
        """
        Performs one round of draft refinement using the LLM.

        Args:
            current_draft: The current draft content or feedback.

        Returns:
            The refined draft suggested by the LLM, or None if an error occurs.
        """
        # Add user's latest input to conversation history
        self.conversation_history.append({"role": "user", "content": current_draft})

        try:
            # Get refined draft from LLM
            response = await self.client.chat_completion(
                model=self.model,
                messages=self.conversation_history,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            # Extract content based on OpenRouter formatting
            if isinstance(response, dict) and 'choices' in response:
                if len(response['choices']) > 0 and 'message' in response['choices'][0]:
                    refined_draft = response['choices'][0]['message']['content']
                    
                    # Add the assistant's response to conversation history
                    self.conversation_history.append({"role": "assistant", "content": refined_draft})
                    return refined_draft.strip()
                
                else:
                    print("Unexpected response format - no message in choice")
                    print(f"Response data: {response}")
                    return None
            else:
                print(f"Unexpected response format: {response}")
                return None

        except Exception as e:
            print(f"Error during LLM call: {e}")
            # Remove the user message that caused the error
            if len(self.conversation_history) > 1 and self.conversation_history[-1]['role'] == 'user':
                self.conversation_history.pop()
            return None

    async def evaluate_draft(self, draft_content: str) -> Dict[str, Any]:
        """
        Evaluate the current draft and provide specific improvement suggestions.

        Args:
            draft_content: The current draft content to evaluate

        Returns:
            Dictionary with evaluation metrics and suggested improvements
        """
        eval_prompt = f"""
        Analyze this draft and provide:
        1. Key strengths
        2. Specific areas needing improvement
        3. Technical accuracy assessment
        4. Structural coherence evaluation
        5. Writing style consistency check

        Draft content:
        {draft_content}
        """

        try:
            response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": eval_prompt}],
                max_tokens=1000,
                temperature=0.5
            )

            if isinstance(response, dict) and 'choices' in response:
                evaluation = response['choices'][0]['message']['content']
                
                # Parse evaluation into structured format
                return {
                    "evaluation_text": evaluation,
                    "meets_standards": "major issues" not in evaluation.lower(),
                    "suggested_improvements": [
                        line.strip() for line in evaluation.split("\n")
                        if line.strip().startswith("-") or line.strip().startswith("*")
                    ]
                }
            
            return {
                "evaluation_text": "Error performing evaluation",
                "meets_standards": False,
                "suggested_improvements": []
            }

        except Exception as e:
            print(f"Error during draft evaluation: {e}")
            return {
                "evaluation_text": f"Evaluation failed: {str(e)}",
                "meets_standards": False,
                "suggested_improvements": []
            }

    async def process_draft(self, request: DraftRequest) -> DraftResponse:
        """
        Process a new draft or feedback for API integration.

        Args:
            request: DraftRequest with draft content and context

        Returns:
            DraftResponse with refined draft and related information
        """
        # Set up report context if this is a new conversation or context changed
        self.set_report_context(request.context)

        # Get the refined draft from the LLM
        refined_draft = await self.refine_draft(request.draft_content)
        if refined_draft is None:
            return DraftResponse(
                refined_draft="Unable to process draft. Please try again with a different draft.",
                is_complete=False,
                suggested_improvements=[]
            )

        # Evaluate the refined draft
        evaluation = await self.evaluate_draft(refined_draft)
        
        return DraftResponse(
            refined_draft=refined_draft,
            is_complete=False,  # Assume one refinement at a time for API
            suggested_improvements=evaluation.get("suggested_improvements", []),
            conversation_id=str(id(self.conversation_history))
        )

    async def finalize_draft(self, conversation_id: str) -> DraftResponse:
        """
        Mark the current draft as approved.

        Args:
            conversation_id: The conversation ID to finalize

        Returns:
            DraftResponse with the final draft and completion status set to True
        """
        if not self.conversation_history or len(self.conversation_history) < 2:
            return DraftResponse(
                refined_draft="No draft has been processed yet.",
                is_complete=False,
                suggested_improvements=[]
            )

        # Get the last assistant message as the final draft
        for message in reversed(self.conversation_history):
            if message["role"] == "assistant":
                final_evaluation = await self.evaluate_draft(message["content"])
                return DraftResponse(
                    refined_draft=message["content"],
                    is_complete=True,
                    suggested_improvements=final_evaluation.get("suggested_improvements", []),
                    conversation_id=conversation_id
                )

        return DraftResponse(
            refined_draft="No refined draft found in conversation history.",
            is_complete=False,
            suggested_improvements=[]
        )


async def refine_draft(request: DraftRequest) -> DraftResponse:
    """
    API endpoint for refining a draft.

    Args:
        request: The draft request containing the content and context

    Returns:
        DraftResponse with the refined draft
    """
    refiner = DraftRefiner()
    response = await refiner.process_draft(request)
    await refiner.client.client.aclose()
    return response

async def approve_draft(conversation_id: str) -> DraftResponse:
    """
    API endpoint for approving the current refined draft.

    Args:
        conversation_id: The ID of the conversation to finalize

    Returns:
        DraftResponse with the final approved draft
    """
    refiner = DraftRefiner()
    response = await refiner.finalize_draft(conversation_id)
    await refiner.client.client.aclose()
    return response

async def test_chat_completion():  #! FOR TESTING ONLY
    """
    Basic test function to verify OpenRouter API connectivity.
    """
    client = OpenRouterClient()
    try:
        print("Testing OpenRouter API connection...")
        response = await client.chat_completion(
            model=REFINER_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": "Briefly explain what makes a good research paper introduction."
                }
            ],
            max_tokens=100,
            temperature=0.7
        )
        print("Test Response:\n", response)
        print("Connection successful!")
        return True
    except Exception as e:
        print(f"Test connection failed: {e}")
        return False
    finally:
        await client.client.aclose()

async def main():  #! FOR CLI TESTING ONLY
    """
    Main function to run the command-line draft refinement tool.
    This provides a CLI testing interface that uses the same code
    as the API but with interactive prompts.
    """
    print("🚀 Starting Draft Refinement Process...")

    # Test connection first
    connection_ok = await test_chat_completion()
    if not connection_ok:
        print("⚠️ Could not connect to OpenRouter API. Please check your API key and connection.")
        return

    # Collect report context information
    print("\nPlease provide report context information:")
    report_type = input("Report Type (e.g., 'Research Paper', 'Technical Report'): ").strip() or "Research Paper"
    
    print("\nSelect Technical Level:")
    print("1) Expert")
    print("2) Advanced")
    print("3) Intermediate")
    level_choice = input("Enter number (1-3): ").strip()
    technical_level = {
        "1": "Expert",
        "2": "Advanced",
        "3": "Intermediate"
    }.get(level_choice, "Advanced")

    target_audience = input("Target Audience: ").strip() or "Technical Professionals"
    length_guidelines = input("Length Guidelines (e.g., '5000 words'): ").strip() or "Standard research paper length"

    # Package context info
    context = ReportContext(
        report_type=report_type,
        technical_level=technical_level,
        target_audience=target_audience,
        length_guidelines=length_guidelines
    )

    # Get initial draft
    print("\nPlease provide your draft content.")
    print("You can paste multiple lines. When finished, press Ctrl+D (Unix) or Ctrl+Z (Windows) followed by Enter.")
    print("Begin typing/pasting your draft:")
    
    draft_lines = []
    while True:
        try:
            line = input()
            draft_lines.append(line)
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nDraft input cancelled.")
            return

    initial_draft = "\n".join(draft_lines)
    if not initial_draft.strip():
        print("Draft cannot be empty. Exiting.")
        return

    # Use the API-compatible methods for consistency
    refiner = DraftRefiner()

    # Initial refinement
    print("\n⏳ Processing initial draft...")
    response = await refiner.process_draft(DraftRequest(
        draft_content=initial_draft,
        context=context
    ))
    
    final_draft = response.refined_draft
    conversation_id = response.conversation_id

    # Feedback-based refinement loop
    while not response.is_complete:
        print("\n================ Current Draft ================")
        print(final_draft)
        print("=============================================")
        
        if response.suggested_improvements:
            print("\nSuggested Improvements:")
            for i, suggestion in enumerate(response.suggested_improvements, 1):
                print(f"{i}. {suggestion}")

        feedback = input("\nIs this draft good? (y/n/provide feedback): ").strip()

        if feedback.lower() == 'y':
            response = await refiner.finalize_draft(conversation_id or "")
            break

        else:  # Use the feedback (or ask for it if just 'n')
            if feedback.lower() == 'n':
                print("\nProvide your feedback. Press Ctrl+D (Unix) or Ctrl+Z (Windows) followed by Enter when done:")
                feedback_lines = []
                while True:
                    try:
                        line = input()
                        feedback_lines.append(line)
                    except EOFError:
                        break
                    except KeyboardInterrupt:
                        print("\nFeedback input cancelled.")
                        continue
                
                feedback = "\n".join(feedback_lines)
                if not feedback.strip():
                    print("No feedback provided, using previous version")
                    continue

            # Process the feedback and get a new refined draft 
            print("\n⏳ Refining draft based on feedback...")
            response = await refiner.process_draft(DraftRequest(
                draft_content=feedback,
                context=context
            ))
            final_draft = response.refined_draft

    # Display final approved draft
    print("\n================ Final Approved Draft ================")
    print(final_draft)
    print("====================================================")
    
    # Provide final evaluation
    print("\nFinal Draft Evaluation:")
    evaluation = await refiner.evaluate_draft(final_draft)
    if evaluation["suggested_improvements"]:
        print("\nConsider these points for future revisions:")
        for suggestion in evaluation["suggested_improvements"]:
            print(f"- {suggestion}")
    else:
        print("\nNo additional improvements suggested.")
    
    print("\nRefinement process complete! The final draft is ready for review.")
    
    await refiner.client.client.aclose()  # Close client connection

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting draft refinement process.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()