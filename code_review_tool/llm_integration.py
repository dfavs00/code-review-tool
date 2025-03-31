"""Integration with Large Language Models for code review."""

from typing import Dict, List, Optional, Any
import os
from abc import ABC, abstractmethod
from pathlib import Path

import openai
from anthropic import Anthropic
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
else:
    print("Warning: .env file not found. Please create one based on .env.example to configure API keys.")

# Constants for providers
PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_GEMINI = "gemini"
PROVIDER_LOCAL = "local"
VALID_PROVIDERS = [PROVIDER_OPENAI, PROVIDER_ANTHROPIC, PROVIDER_GEMINI, PROVIDER_LOCAL]

# Constants for default models
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_ANTHROPIC_MODEL = "claude-3-opus-20240229"
DEFAULT_GEMINI_MODEL = "gemini-1.5-pro"

# Constants for environment variables
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
ENV_GOOGLE_API_KEY = "GOOGLE_API_KEY"

# Constants for generation parameters
GENERATION_TEMPERATURE = 0.2
GENERATION_MAX_TOKENS = 2000

# Constants for prompts
SYSTEM_PROMPT = "You are a helpful code review assistant. Provide constructive feedback on the code changes."

# ModelProvider type
# Using str instead of Literal for better compatibility with Typer
ModelProvider = str  # Possible values: "openai", "anthropic", "gemini", "local"


class LLMClient(ABC):
    """Abstract base class for LLM clients.
    
    This class defines the interface for interacting with different LLM providers.
    """
    
    @abstractmethod
    def generate_review(self, code_context: Dict[str, Any]) -> str:
        """Generate a code review based on the provided code context.
        
        Args:
            code_context: Dictionary containing code changes and context.
            
        Returns:
            The generated review as a string.
        """
        pass
    
    def _create_prompt(self, code_context: Dict[str, Any]) -> str:
        """Create a prompt for the code review.
        
        Args:
            code_context: Dictionary containing code changes and context.
            
        Returns:
            The prompt as a string.
        """
        prompt_parts = ["Please review the following code changes:"]
        
        # Add each file's changes to the prompt
        for file_path, file_info in code_context.items():
            prompt_parts.append(f"\n## File: {file_path}")
            
            if file_info['is_new_file']:
                prompt_parts.append("(New file)")
            
            # Add each change with its context
            for change in file_info['changes']:
                prompt_parts.append(f"\nStarting at line {change['start_line']}:")
                prompt_parts.append("```")
                prompt_parts.extend(change['lines'])
                prompt_parts.append("```")
        
        # Add instructions for the review
        prompt_parts.append("\n\nPlease provide a code review that includes the following bullet points:")
        prompt_parts.append("1. Overall assessment of the changes")
        prompt_parts.append("2. Specific issues or concerns")
        prompt_parts.append("3. Suggestions for improvement")
        prompt_parts.append("4. Best practices that should be followed")
        prompt_parts.append("5. Any potential bugs or edge cases")
        prompt_parts.append("6. At the end add a short poem related to crocodiles and the code changes")
        
        # Add severity classification instructions
        prompt_parts.append("\nIn addition, for all the above steps, please preface review lines with this naming system to indicate severity so I can parse the output:")
        prompt_parts.append("Severity Naming System for Code Review:")
        prompt_parts.append("Please preface each review comment with one of these severity levels and a keyword in brackets, e.g., '[high:critical]' or '[medium:recommend]'. Use the following guidelines to choose the severity and keyword:")
        prompt_parts.append("- High Severity (urgent issues requiring immediate attention):")
        prompt_parts.append("  - critical, severe, major, important, significant, serious, dangerous, urgent, must, required, security, vulnerability, crash, error, bug, broken, incorrect, wrong, fail, failure")
        prompt_parts.append("- Medium Severity (notable issues that should be addressed):")
        prompt_parts.append("  - moderate, consider, should, recommend, improvement, enhance, better, issue, problem, concern, attention, review, update, change, modify, refactor, restructure, reorganize")
        prompt_parts.append("- Low Severity (minor or optional suggestions):")
        prompt_parts.append("  - minor, trivial, style, nit, suggestion, cosmetic, optional, might, could, perhaps, consider, preference, opinion, personal, taste, readability, clarity, documentation, comment")
        
        return "\n".join(prompt_parts)


class OpenAIClient(LLMClient):
    """Client for interacting with OpenAI's language models."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_OPENAI_MODEL) -> None:
        """Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key. If None, uses the OPENAI_API_KEY environment variable.
            model: The model to use for code review.
        """
        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get(ENV_OPENAI_API_KEY)
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and not found in environment")
        
        # Set up the client
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model
    
    def generate_review(self, code_context: Dict[str, Any]) -> str:
        """Generate a code review using OpenAI's language model.
        
        Args:
            code_context: Dictionary containing code changes and context.
            
        Returns:
            The generated review as a string.
        """
        # Create a prompt for the code review
        prompt = self._create_prompt(code_context)
        
        # Generate the review
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=GENERATION_TEMPERATURE,
            max_tokens=GENERATION_MAX_TOKENS
        )
        
        # Extract and return the review text
        return response.choices[0].message.content


class AnthropicClient(LLMClient):
    """Client for interacting with Anthropic's language models."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_ANTHROPIC_MODEL) -> None:
        """Initialize the Anthropic client.
        
        Args:
            api_key: Anthropic API key. If None, uses the ANTHROPIC_API_KEY environment variable.
            model: The model to use for code review.
        """
        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get(ENV_ANTHROPIC_API_KEY)
        if not self.api_key:
            raise ValueError("Anthropic API key not provided and not found in environment")
        
        # Set up the client
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
    
    def generate_review(self, code_context: Dict[str, Any]) -> str:
        """Generate a code review using Anthropic's language model.
        
        Args:
            code_context: Dictionary containing code changes and context.
            
        Returns:
            The generated review as a string.
        """
        # Create a prompt for the code review
        prompt = self._create_prompt(code_context)
        
        # Generate the review
        response = self.client.messages.create(
            model=self.model,
            max_tokens=GENERATION_MAX_TOKENS,
            temperature=GENERATION_TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract and return the review text
        return response.content[0].text


class GeminiClient(LLMClient):
    """Client for interacting with Google's Gemini models."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_GEMINI_MODEL) -> None:
        """Initialize the Gemini client.
        
        Args:
            api_key: Google API key. If None, uses the GOOGLE_API_KEY environment variable.
            model: The model to use for code review.
        """
        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get(ENV_GOOGLE_API_KEY)
        if not self.api_key:
            raise ValueError("Google API key not provided and not found in environment")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Set the model
        self.model = model
    
    def generate_review(self, code_context: Dict[str, Any]) -> str:
        """Generate a code review using Google's Gemini model.
        
        Args:
            code_context: Dictionary containing code changes and context.
            
        Returns:
            The generated review as a string.
        """
        # Create a prompt for the code review
        prompt = self._create_prompt(code_context)
        
        # Get the model
        model = genai.GenerativeModel(self.model)
        
        # Create a preamble that includes the system message since Gemini doesn't support system role
        preamble = f"{SYSTEM_PROMPT}\n\n"
        full_prompt = preamble + prompt
        
        # Generate the review - Gemini doesn't support system role, so we use a different approach
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": GENERATION_TEMPERATURE,
                "max_output_tokens": GENERATION_MAX_TOKENS
            }
        )
        
        # Extract and return the review text
        return response.text


def get_llm_client(provider: ModelProvider, api_key: Optional[str] = None, model: Optional[str] = None) -> LLMClient:
    """Factory function to get an LLM client based on the provider.
    
    Args:
        provider: The LLM provider to use.
        api_key: API key for the provider. If None, uses environment variables.
        model: The model to use. If None, uses the default model for the provider.
        
    Returns:
        An instance of the appropriate LLM client.
        
    Raises:
        ValueError: If the provider is not supported.
    """
    # Validate the provider string since we're using a regular string instead of Literal
    if provider not in VALID_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {provider}. Must be one of {VALID_PROVIDERS}")
        
    if provider == PROVIDER_OPENAI:
        return OpenAIClient(api_key=api_key, model=model or DEFAULT_OPENAI_MODEL)
    elif provider == PROVIDER_ANTHROPIC:
        return AnthropicClient(api_key=api_key, model=model or DEFAULT_ANTHROPIC_MODEL)
    elif provider == PROVIDER_GEMINI:
        return GeminiClient(api_key=api_key, model=model or DEFAULT_GEMINI_MODEL)
    elif provider == PROVIDER_LOCAL:
        # Local model support not yet implemented
        raise NotImplementedError("Local model support is not yet implemented")
