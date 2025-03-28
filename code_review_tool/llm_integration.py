"""Integration with Large Language Models for code review."""

from typing import Dict, List, Optional, Any
import os
from abc import ABC, abstractmethod

import openai
from anthropic import Anthropic


# ModelProvider type
# Using str instead of Literal for better compatibility with Typer
ModelProvider = str  # Possible values: "openai", "anthropic", "local"


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


class OpenAIClient(LLMClient):
    """Client for interacting with OpenAI's language models."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4") -> None:
        """Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key. If None, uses the OPENAI_API_KEY environment variable.
            model: The model to use for code review.
        """
        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
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
                {"role": "system", "content": "You are a helpful code review assistant. Provide constructive feedback on the code changes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # Lower temperature for more consistent reviews
            max_tokens=2000
        )
        
        # Extract and return the review text
        return response.choices[0].message.content
    
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
        prompt_parts.append("\n\nPlease provide a code review that includes:")
        prompt_parts.append("1. Overall assessment of the changes")
        prompt_parts.append("2. Specific issues or concerns")
        prompt_parts.append("3. Suggestions for improvement")
        prompt_parts.append("4. Best practices that should be followed")
        prompt_parts.append("5. Any potential bugs or edge cases")
        
        return "\n".join(prompt_parts)


class AnthropicClient(LLMClient):
    """Client for interacting with Anthropic's language models."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229") -> None:
        """Initialize the Anthropic client.
        
        Args:
            api_key: Anthropic API key. If None, uses the ANTHROPIC_API_KEY environment variable.
            model: The model to use for code review.
        """
        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
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
            max_tokens=2000,
            temperature=0.2,
            system="You are a helpful code review assistant. Provide constructive feedback on the code changes.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract and return the review text
        return response.content[0].text
    
    def _create_prompt(self, code_context: Dict[str, Any]) -> str:
        """Create a prompt for the code review.
        
        Args:
            code_context: Dictionary containing code changes and context.
            
        Returns:
            The prompt as a string.
        """
        # Use the same prompt format as OpenAI for consistency
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
        prompt_parts.append("\n\nPlease provide a code review that includes:")
        prompt_parts.append("1. Overall assessment of the changes")
        prompt_parts.append("2. Specific issues or concerns")
        prompt_parts.append("3. Suggestions for improvement")
        prompt_parts.append("4. Best practices that should be followed")
        prompt_parts.append("5. Any potential bugs or edge cases")
        
        return "\n".join(prompt_parts)


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
    valid_providers = ["openai", "anthropic", "local"]
    if provider not in valid_providers:
        raise ValueError(f"Unsupported LLM provider: {provider}. Must be one of {valid_providers}")
        
    if provider == "openai":
        return OpenAIClient(api_key=api_key, model=model or "gpt-4")
    elif provider == "anthropic":
        return AnthropicClient(api_key=api_key, model=model or "claude-3-opus-20240229")
    elif provider == "local":
        # Local model support not yet implemented
        raise NotImplementedError("Local model support is not yet implemented")
