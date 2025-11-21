"""Base class and utilities for LLM clients."""
import json
import logging
import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Base class for LLM-based clients with common OpenAI initialization."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview"
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: LLM model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY env var or pass api_key.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model


def make_llm_call(
    client: OpenAI,
    model: str,
    system_message: str,
    user_message: str,
    response_format: Optional[Dict[str, str]] = None,
    temperature: float = 0.3,
    json_response: bool = False
) -> str:
    """
    Make a standardized LLM API call with error handling.
    
    Args:
        client: OpenAI client instance
        model: Model to use
        system_message: System message for the LLM
        user_message: User message/prompt
        response_format: Optional response format (e.g., {"type": "json_object"})
        temperature: Temperature setting
        json_response: If True, parse response as JSON and return string representation
    
    Returns:
        Response content as string
    
    Raises:
        Exception: If the API call fails
    """
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    
    if response_format:
        kwargs["response_format"] = response_format
    
    try:
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```", 2)[-1].rsplit("```", 1)[0].strip()
        
        return content
    except Exception as e:
        logger.error(f"Error during LLM API call: {e}", exc_info=True)
        raise


def make_json_llm_call(
    client: OpenAI,
    model: str,
    system_message: str,
    user_message: str,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Make an LLM API call expecting JSON response.
    
    Args:
        client: OpenAI client instance
        model: Model to use
        system_message: System message for the LLM
        user_message: User message/prompt
        temperature: Temperature setting
    
    Returns:
        Parsed JSON response as dictionary
    
    Raises:
        Exception: If the API call fails or response is not valid JSON
    """
    content = make_llm_call(
        client=client,
        model=model,
        system_message=system_message,
        user_message=user_message,
        response_format={"type": "json_object"},
        temperature=temperature,
        json_response=True
    )
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise ValueError(f"Invalid JSON response from LLM: {e}")

