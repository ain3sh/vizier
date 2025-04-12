"""
OpenRouter API client for interacting with AI models through OpenRouter's service.

This module provides a clean interface for:
- Listing available models with filtering options
- Making chat completion requests with full parameter support
- Using tools/function calling with models
"""

import os
from typing import Dict, List, Optional, Union, Any, Literal
import httpx
import json
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException

load_dotenv(find_dotenv("key.env")) # load env vars

# api constants
DEFAULT_API_BASE = "https://openrouter.ai/api/v1"
DEFAULT_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


class ProviderSortOptions(str, Enum):
    """Sort options for provider routing"""
    PRICE = "price"
    THROUGHPUT = "throughput"
    LATENCY = "latency"

class DataCollectionPolicy(str, Enum):
    """Provider data collection policy options"""
    ALLOW = "allow"
    DENY = "deny"

class ProviderPreferences(BaseModel):
    """Configuration for provider routing preferences"""
    order: Optional[List[str]] = None
    allow_fallbacks: Optional[bool] = None
    require_parameters: Optional[bool] = None
    data_collection: Optional[DataCollectionPolicy] = None
    ignore: Optional[List[str]] = None
    quantizations: Optional[List[str]] = None
    sort: Optional[ProviderSortOptions] = None

class ToolCall(BaseModel):
    """Representation of a tool call"""
    id: str
    type: str
    function: Dict[str, Any]

class FunctionCall(BaseModel):
    """Function call definition"""
    name: str
    arguments: str

class FunctionDescription(BaseModel):
    """Description of a function tool"""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any]

class Tool(BaseModel):
    """Tool definition for model usage"""
    type: str = "function"
    function: FunctionDescription

class ReasoningConfig(BaseModel):
    """Configuration for reasoning tokens"""
    max_tokens: Optional[int] = None
    effort: Optional[Literal["high", "medium", "low"]] = None
    exclude: Optional[bool] = None

class ChatMessage(BaseModel):
    """Chat message format"""
    role: str
    content: Union[str, List[Dict[str, Any]]]
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class OpenRouterClient:
    """
    Client for interacting with OpenRouter's API.

    This class provides methods for listing models, making chat completions,
    and other operations supported by OpenRouter, using the OpenAI SDK format.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_API_BASE,
        timeout: int = 60,
        app_name: Optional[str] = None,
    ):
        """
        Initialize the OpenRouter client.

        Args:
            api_key: OpenRouter API key [defaults to OPENROUTER_API_KEY env var]
            base_url: API base URL [defaults to OpenRouter API v1]
            timeout: Request timeout in seconds
            app_name: Optional app name to include in requests for tracking
        """
        self.api_key = api_key or DEFAULT_API_KEY
        self.base_url = base_url
        self.timeout = timeout
        self.app_name = app_name

        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable or pass it to the constructor.")

        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

        # add app name header
        if not self.app_name:
            self.app_name = "Vizier"
        self.client.headers["X-Title"] = self.app_name


    async def list_models(
        self,
        filter_by: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        List available models from OpenRouter with optional filtering.

        Args:
            filter_by: Optional dictionary of filters to apply. Supported filters include:
                - provider: Filter by provider name (e.g., "openai", "anthropic")
                - max_price: Maximum price per token (e.g., 0.01)
                - min_context_length: Minimum context length (e.g., 8192)
                - feature: Specific feature support (e.g., "tool_calls", "vision")

        Returns:
            Dictionary containing model information.
        """
        url = f"{self.base_url}/models"

        # apply filters via query params if specified
        params = {}
        if filter_by:
            if "provider" in filter_by:
                params["provider"] = filter_by["provider"]
            if "max_price" in filter_by:
                params["max_price"] = filter_by["max_price"]
            if "min_context_length" in filter_by:
                params["min_context"] = filter_by["min_context_length"]
            if "feature" in filter_by:
                params["feature"] = filter_by["feature"]

        response = await self.client.get(url, params=params)

        if response.status_code != 200: # 200: OK
            self._handle_error_response(response)

        return response.json()


    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, str]] = None,
        stop: Optional[Union[str, List[str]]] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        provider: Optional[Dict[str, Any]] = None,
        transforms: Optional[List[str]] = None,
        reasoning: Optional[Dict[str, Any]] = None,
        max_price: Optional[Dict[str, float]] = None,
        plugins: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a chat completion using the specified model.

        Args:
            model: Model identifier (e.g., "openai/gpt-4o")
            messages: List of message dictionaries with role and content
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter (0-1)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            tools: List of tools/functions the model can use
            tool_choice: Control for tool usage ("auto", "none" or specific tool)
            response_format: Format for the response (e.g., {"type": "json_object"})
            stop: Sequences where the API will stop generating
            frequency_penalty: Penalty for token frequency (-2 to 2)
            presence_penalty: Penalty for token presence (-2 to 2)
            seed: Random seed for deterministic outputs
            provider: Provider routing preferences
            transforms: Transformations to apply (e.g., ["middle-out"])
            reasoning: Configuration for reasoning tokens
            max_price: Maximum price constraints
            plugins: List of plugins to use (e.g., web search)

        Returns:
            Chat completion response
        """
        url = f"{self.base_url}/chat/completions"

        # build request payload
        payload = {
            "model": model,
            "messages": messages
        }

        # add optional params if specified
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stream:
            payload["stream"] = stream
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        if response_format:
            payload["response_format"] = response_format
        if stop:
            payload["stop"] = stop
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if seed is not None:
            payload["seed"] = seed
        if provider:
            payload["provider"] = provider
        if transforms:
            payload["transforms"] = transforms
        if reasoning:
            payload["reasoning"] = reasoning
        if max_price:
            payload["max_price"] = max_price
        if plugins:
            payload["plugins"] = plugins

        response = await self.client.post(url, json=payload)
        if response.status_code != 200: # 200: OK
            self._handle_error_response(response)

        return response.json()

    async def get_generation_details(self, generation_id: str) -> Dict[str, Any]:
        """
        Retrieve details about a specific generation, including tokens and cost.

        Args:
            generation_id: The generation ID to query

        Returns:
            Generation details including token counts, costs, and other metadata
        """
        url = f"{self.base_url}/generation"
        params = {"id": generation_id}

        response = await self.client.get(url, params=params)
        if response.status_code != 200: # 200: OK
            self._handle_error_response(response)

        return response.json()

    async def get_credits(self) -> Dict[str, Any]:
        """
        Get information about your OpenRouter credit balance.

        Returns:
            Dictionary containing credit information
        """
        url = f"{self.base_url}/credits"

        response = await self.client.get(url)
        if response.status_code != 200: # 200: OK
            self._handle_error_response(response)

        return response.json()

    def _handle_error_response(self, response: httpx.Response) -> None:
        """
        Handle error responses from the API.

        Args:
            response: The error response from the API

        Raises:
            Exception with error details
        """
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            error_type = error_data.get("error", {}).get("type", "api_error")
            error_code = response.status_code

            raise Exception(f"OpenRouter API Error ({error_code}): {error_message} - {error_type}")
        except json.JSONDecodeError:
            raise Exception(f"OpenRouter API Error ({response.status_code}): {response.text}")




# create FastAPI router endpoints for OpenRouter integration
router = APIRouter(
    prefix="/openrouter",
    tags=["openrouter"],
    responses={404: {"description": "Not found"}},
)

# factory function to create OpenRouterClient instance
async def get_openrouter_client(
    api_key: Optional[str] = None,
    app_name: Optional[str] = None
) -> OpenRouterClient:
    """Create and return an OpenRouterClient instance."""
    return OpenRouterClient(api_key=api_key, app_name=app_name)

@router.get("/models")
async def list_models(
    provider: Optional[str] = None,
    max_price: Optional[float] = None,
    min_context_length: Optional[int] = None,
    feature: Optional[str] = None,
    client: OpenRouterClient = Depends(get_openrouter_client)
):
    """
    List available models with optional filters.

    Args:
        provider: Filter by provider name (e.g., "openai", "anthropic")
        max_price: Maximum price per token
        min_context_length: Minimum context length
        feature: Required feature support (e.g., "tool_calls", "vision")

    Returns:
        List of matching models
    """
    filters = {}
    if provider:
        filters["provider"] = provider
    if max_price:
        filters["max_price"] = max_price
    if min_context_length:
        filters["min_context_length"] = min_context_length
    if feature:
        filters["feature"] = feature

    try:
        models = await client.list_models(filter_by=filters)
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/completions")
async def create_chat_completion(
    request: Dict[str, Any],
    client: OpenRouterClient = Depends(get_openrouter_client)
):
    """
    Create a chat completion using the specified parameters.

    The request body should include model, messages, and any optional parameters
    supported by OpenRouter's chat completion endpoint.

    Returns:
        Chat completion response
    """
    try:
        # extract required params
        model = request.pop("model")
        messages = request.pop("messages")

        # pass remaining params as kwargs
        response = await client.chat_completion(model=model, messages=messages, **request)
        return response

    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/credits")
async def get_credits(
    client: OpenRouterClient = Depends(get_openrouter_client)
):
    """
    Get information about your OpenRouter credit balance.

    Returns:
        Credit information including balance
    """
    try:
        return await client.get_credits()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/generation/{generation_id}")
async def get_generation(
    generation_id: str,
    client: OpenRouterClient = Depends(get_openrouter_client)
):
    """
    Get details about a specific generation.

    Args:
        generation_id: ID of the generation to retrieve

    Returns:
        Generation details including token usage and costs
    """
    try:
        return await client.get_generation_details(generation_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))