"""Command-line interface for the AI code review tool."""

from typing import Optional, List, Dict, Any
import os
import sys

import typer
from rich.console import Console
from rich.markdown import Markdown

from code_review_tool.git_client import GitClient
from code_review_tool.diff_parser import DiffParser
from code_review_tool.llm_integration import get_llm_client, ModelProvider
from code_review_tool.feedback_processor import FeedbackProcessor


# Create Typer app
app = typer.Typer(
    name="code-review-tool",
    help="AI-powered code review tool that analyzes Git diffs and provides feedback."
)

# Create console for rich output
console = Console()


@app.command("review")
def review(
    target_branch: str = typer.Argument(
        ...,
        help="The target branch to compare against (e.g., 'main' or 'master')."
    ),
    current_branch: Optional[str] = typer.Option(
        None,
        "--branch", "-b",
        help="The current branch to review. If not specified, uses the active branch."
    ),
    repo_path: Optional[str] = typer.Option(
        None,
        "--repo", "-r",
        help="Path to the Git repository. If not specified, uses the current directory."
    ),
    model_provider: str = typer.Option(
        "openai",
        "--provider", "-p",
        help="The LLM provider to use for code review (openai, anthropic, or local)."
    ),
    model_name: Optional[str] = typer.Option(
        None,
        "--model", "-m",
        help="The specific model to use for code review. If not specified, uses the default model for the provider."
    ),
    output_format: str = typer.Option(
        "markdown",
        "--format", "-f",
        help="The output format for the review (text, markdown, or json)."
    ),
    output_file: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Path to save the review output. If not specified, prints to console."
    ),
    context_lines: int = typer.Option(
        3,
        "--context", "-c",
        help="Number of context lines to include around changes."
    ),
) -> None:
    """Review code changes between Git branches using AI.
    
    This command analyzes the differences between the current branch and a target branch,
    sends the relevant code to a language model, and presents structured feedback.
    """
    try:
        # Initialize components
        git_client = GitClient(repo_path)
        diff_parser = DiffParser()
        feedback_processor = FeedbackProcessor()
        
        # Get the diff between branches
        console.print(f"Fetching diff between [bold]{target_branch}[/bold] and "
                      f"[bold]{current_branch or 'current branch'}[/bold]...")
        diff = git_client.get_diff(target_branch, current_branch)
        
        # Parse the diff
        console.print("Parsing code changes...")
        file_diffs = diff_parser.parse_diff(diff)
        
        # Extract code context
        code_context = diff_parser.extract_code_context(file_diffs, context_lines)
        
        # Check if there are any changes to review
        if not code_context:
            console.print("[yellow]No code changes found to review.[/yellow]")
            return
        
        # Get the LLM client
        console.print(f"Using [bold]{model_provider}[/bold] for code review...")
        llm_client = get_llm_client(model_provider, model=model_name)
        
        # Generate the review
        console.print("Generating code review...")
        try:
            raw_feedback = llm_client.generate_review(code_context)
        except Exception as e:
            if "insufficient_quota" in str(e):
                console.print("[bold red]Error:[/bold red] Your OpenAI account has exceeded its quota. Please check your billing details.")
                console.print("You can try using a different provider with --provider anthropic (requires an Anthropic API key).")
            elif "model_not_found" in str(e):
                console.print("[bold red]Error:[/bold red] The specified model is not available with your API key.")
                console.print("Try using a different model with --model gpt-3.5-turbo or a different provider with --provider anthropic.")
            else:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
            sys.exit(1)
        
        # Process the feedback
        console.print("Processing feedback...")
        feedback_items = feedback_processor.process_feedback(raw_feedback)
        
        # Format the feedback
        formatted_feedback = feedback_processor.format_feedback(feedback_items, output_format)
        
        # Output the feedback
        if output_file:
            # Save to file
            with open(output_file, "w") as f:
                f.write(formatted_feedback)
            console.print(f"Review saved to [bold]{output_file}[/bold]")
        else:
            # Print to console
            if output_format == "markdown":
                console.print(Markdown(formatted_feedback))
            else:
                console.print(formatted_feedback)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command("config")
def config(
    set_api_key: Optional[str] = typer.Option(
        None,
        "--set-api-key",
        help="Set the API key for the specified provider."
    ),
    provider: Optional[ModelProvider] = typer.Option(
        None,
        "--provider", "-p",
        help="The LLM provider (openai, anthropic, or local)."
    ),
    show: bool = typer.Option(
        False,
        "--show",
        help="Show the current configuration."
    ),
) -> None:
    """Configure the code review tool.
    
    This command allows you to set API keys and view the current configuration.
    """
    # TODO: Implement configuration management
    console.print("[yellow]Configuration management not yet implemented.[/yellow]")


def main() -> None:
    """Main entry point for the CLI application."""
    app()
