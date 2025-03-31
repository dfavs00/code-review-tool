"""Command-line interface for the AI code review tool."""

from typing import Optional, List, Dict, Any, Set
import os
import sys

import typer
from rich.console import Console
from rich.markdown import Markdown

from code_review_tool.git_client import GitClient
from code_review_tool.diff_parser import DiffParser
from code_review_tool.llm_integration import get_llm_client, ModelProvider
from code_review_tool.feedback_processor import FeedbackProcessor
from code_review_tool.utils import save_review_history, count_lines_by_type, get_timestamp


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
        help="The LLM provider to use for code review (openai, anthropic, gemini, or local)."
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
    auto_save_markdown: bool = typer.Option(
        True,
        "--auto-save/--no-auto-save",
        help="Automatically save a timestamped markdown file in addition to console output."
    ),
    context_lines: int = typer.Option(
        3,
        "--context", "-c",
        help="Number of context lines to include around changes."
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output for debugging."
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
        
        # Print verbose output if requested
        if verbose:
            console.print("[bold]Raw diff:[/bold]")
            console.print(diff)
        
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
            
            # Print raw feedback in verbose mode
            if verbose:
                console.print("[bold]Raw LLM response:[/bold]")
                console.print(raw_feedback)
                
        except Exception as e:
            if "insufficient_quota" in str(e):
                console.print("[bold red]Error:[/bold red] Your OpenAI account has exceeded its quota. Please check your billing details.")
                console.print("You can try using a different provider with --provider anthropic or --provider gemini (requires respective API keys).")
            elif "model_not_found" in str(e):
                console.print("[bold red]Error:[/bold red] The specified model is not available with your API key.")
                console.print("Try using a different model with --model gpt-3.5-turbo or a different provider with --provider anthropic or --provider gemini.")
            elif "Google API key not provided" in str(e):
                console.print("[bold red]Error:[/bold red] Google API key not provided or not found in environment.")
                console.print("Please add your Google API key to the .env file as GOOGLE_API_KEY=your_key_here.")
            else:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
            sys.exit(1)
        
        # Process the feedback
        console.print("Processing feedback...")
        feedback_items = feedback_processor.process_feedback(raw_feedback)
        
        # Format the feedback
        formatted_feedback = feedback_processor.format_feedback(feedback_items, output_format)
        
        # Generate a timestamped filename for markdown output
        timestamp = get_timestamp()
        default_md_filename = f"code_review_{timestamp}.md"
        
        # Save review history if verbose mode is enabled
        if verbose:
            # Collect review metadata
            review_metadata = {
                "timestamp": timestamp,
                "target_branch": target_branch,
                "current_branch": current_branch or "current",
                "model_provider": model_provider,
                "model_name": model_name,
                "stats": count_lines_by_type(diff),
                "raw_feedback": raw_feedback,
                "processed_items": [{
                    "category": item.category.value,
                    "file_path": item.file_path,
                    "line_number": item.line_number,
                    "severity": item.severity,
                    "message": item.message
                } for item in feedback_items]
            }
            
            # Save the history
            history_file = save_review_history(review_metadata)
            console.print(f"Review history saved to [bold]{history_file}[/bold]")
        
        # Output the feedback
        if output_file:
            # Save to file with UTF-8 encoding to support emoji and special characters
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_feedback)
            console.print(f"Review saved to [bold]{output_file}[/bold]")
        else:
            # Print to console
            if output_format == "markdown":
                console.print(Markdown(formatted_feedback))
                
                # Also save to a markdown file in the current directory if auto_save_markdown is True
                if auto_save_markdown:
                    with open(default_md_filename, "w", encoding="utf-8") as f:
                        f.write(formatted_feedback)
                    console.print(f"\nReview also saved to [bold]{default_md_filename}[/bold]")
            else:
                console.print(formatted_feedback)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command("compare")
def compare(
    review_files: List[str] = typer.Argument(
        ...,
        help="List of review files to compare."
    ),
    output_file: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Path to save the comparison output. If not specified, prints to console."
    ),
    output_format: str = typer.Option(
        "markdown",
        "--format", "-f",
        help="The output format for the comparison (text, markdown, or json)."
    ),
) -> None:
    """Compare multiple code review files to identify trends and patterns.
    
    This command analyzes multiple review files and generates a comparison report
    highlighting common issues, improvements over time, and overall trends.
    """
    try:
        # Check if files exist
        missing_files = [file for file in review_files if not os.path.exists(file)]
        if missing_files:
            console.print(f"[bold red]Error:[/bold red] The following files do not exist: {', '.join(missing_files)}")
            sys.exit(1)
            
        # Load review files
        console.print(f"Loading {len(review_files)} review files...")
        reviews = []
        
        for file_path in review_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Determine file type based on extension
                if file_path.endswith(".json"):
                    import json
                    # For JSON files, parse the JSON content
                    try:
                        review_data = json.loads(content)
                        reviews.append({
                            "file_path": file_path,
                            "format": "json",
                            "content": review_data
                        })
                    except json.JSONDecodeError:
                        console.print(f"[bold yellow]Warning:[/bold yellow] Could not parse {file_path} as JSON. Skipping.")
                else:
                    # For text/markdown files, parse the content
                    reviews.append({
                        "file_path": file_path,
                        "format": "text",
                        "content": content
                    })
        
        if not reviews:
            console.print("[bold yellow]No valid review files found.[/bold yellow]")
            return
            
        # Generate comparison report
        console.print("Generating comparison report...")
        comparison_report = _generate_comparison_report(reviews, output_format)
        
        # Output the comparison
        if output_file:
            # Save to file with UTF-8 encoding
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(comparison_report)
            console.print(f"Comparison saved to [bold]{output_file}[/bold]")
        else:
            # Print to console
            if output_format == "markdown":
                console.print(Markdown(comparison_report))
            else:
                console.print(comparison_report)
                
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


def _generate_comparison_report(reviews: List[Dict[str, Any]], format_type: str) -> str:
    """Generate a comparison report from multiple reviews.
    
    Args:
        reviews: List of review data dictionaries.
        format_type: The output format (text, markdown, or json).
        
    Returns:
        The formatted comparison report.
    """
    # Extract common issues and categories across reviews
    categories = set()
    issues_by_category = {}
    file_paths = set()
    
    for review in reviews:
        if review["format"] == "json":
            # For JSON reviews, extract from structured data
            for item in review["content"].get("processed_items", []):
                category = item.get("category", "general")
                categories.add(category)
                
                if category not in issues_by_category:
                    issues_by_category[category] = []
                    
                issues_by_category[category].append({
                    "file_path": item.get("file_path"),
                    "message": item.get("message"),
                    "severity": item.get("severity", "medium"),
                    "review_file": review["file_path"]
                })
                
                if item.get("file_path"):
                    file_paths.add(item.get("file_path"))
        else:
            # For text/markdown reviews, we'd need more sophisticated parsing
            # This is a simplified implementation
            pass
    
    # Format the comparison report based on the requested format
    if format_type == "markdown":
        return _format_comparison_as_markdown(reviews, categories, issues_by_category, file_paths)
    elif format_type == "json":
        return _format_comparison_as_json(reviews, categories, issues_by_category, file_paths)
    else:  # text
        return _format_comparison_as_text(reviews, categories, issues_by_category, file_paths)


def _format_comparison_as_markdown(reviews: List[Dict[str, Any]], categories: Set[str], 
                                 issues_by_category: Dict[str, List[Dict[str, Any]]], 
                                 file_paths: Set[str]) -> str:
    """Format the comparison report as markdown.
    
    Args:
        reviews: List of review data dictionaries.
        categories: Set of feedback categories found across reviews.
        issues_by_category: Dictionary of issues grouped by category.
        file_paths: Set of file paths mentioned in the reviews.
        
    Returns:
        The formatted comparison as markdown.
    """
    output_parts = ["# Code Review Comparison\n"]
    
    # Add summary of reviews
    output_parts.append("## Reviews Analyzed")
    for i, review in enumerate(reviews, 1):
        output_parts.append(f"{i}. **{os.path.basename(review['file_path'])}**")
    output_parts.append("")
    
    # Add summary of categories
    output_parts.append("## Categories Found")
    for category in sorted(categories):
        category_issues = issues_by_category.get(category, [])
        output_parts.append(f"- **{category.title()}**: {len(category_issues)} issues")
    output_parts.append("")
    
    # Add summary by file
    if file_paths:
        output_parts.append("## Files with Issues")
        file_issues = {}
        
        for category, issues in issues_by_category.items():
            for issue in issues:
                file_path = issue.get("file_path")
                if file_path:
                    if file_path not in file_issues:
                        file_issues[file_path] = []
                    file_issues[file_path].append(issue)
        
        for file_path, issues in sorted(file_issues.items()):
            output_parts.append(f"### `{file_path}`")
            output_parts.append(f"Total issues: {len(issues)}")
            
            # Group by severity
            high_issues = [i for i in issues if i.get("severity") == "high"]
            medium_issues = [i for i in issues if i.get("severity") == "medium"]
            low_issues = [i for i in issues if i.get("severity") == "low"]
            
            if high_issues:
                output_parts.append(f"- **High severity**: {len(high_issues)} issues")
            if medium_issues:
                output_parts.append(f"- **Medium severity**: {len(medium_issues)} issues")
            if low_issues:
                output_parts.append(f"- **Low severity**: {len(low_issues)} issues")
                
            output_parts.append("")
    
    # Add detailed breakdown by category
    output_parts.append("## Detailed Breakdown by Category")
    
    for category in sorted(categories):
        category_issues = issues_by_category.get(category, [])
        if not category_issues:
            continue
            
        output_parts.append(f"### {category.title()}")
        
        # Group by severity for this category
        high_issues = [i for i in category_issues if i.get("severity") == "high"]
        medium_issues = [i for i in category_issues if i.get("severity") == "medium"]
        low_issues = [i for i in category_issues if i.get("severity") == "low"]
        
        if high_issues:
            output_parts.append("#### [HIGH] Issues")
            for issue in high_issues:
                file_info = f" in `{issue['file_path']}`" if issue.get("file_path") else ""
                output_parts.append(f"- {issue['message'].splitlines()[0]}{file_info}")
            output_parts.append("")
            
        if medium_issues:
            output_parts.append("#### [MEDIUM] Issues")
            for issue in medium_issues:
                file_info = f" in `{issue['file_path']}`" if issue.get("file_path") else ""
                output_parts.append(f"- {issue['message'].splitlines()[0]}{file_info}")
            output_parts.append("")
            
        if low_issues:
            output_parts.append("#### [LOW] Issues")
            for issue in low_issues:
                file_info = f" in `{issue['file_path']}`" if issue.get("file_path") else ""
                output_parts.append(f"- {issue['message'].splitlines()[0]}{file_info}")
            output_parts.append("")
    
    return "\n".join(output_parts)


def _format_comparison_as_text(reviews: List[Dict[str, Any]], categories: Set[str], 
                             issues_by_category: Dict[str, List[Dict[str, Any]]], 
                             file_paths: Set[str]) -> str:
    """Format the comparison report as plain text.
    
    Args:
        reviews: List of review data dictionaries.
        categories: Set of feedback categories found across reviews.
        issues_by_category: Dictionary of issues grouped by category.
        file_paths: Set of file paths mentioned in the reviews.
        
    Returns:
        The formatted comparison as plain text.
    """
    # Simplified implementation - in a real application, this would be more robust
    output_parts = ["CODE REVIEW COMPARISON\n", "Reviews Analyzed:"]
    
    for i, review in enumerate(reviews, 1):
        output_parts.append(f"{i}. {os.path.basename(review['file_path'])}")
    
    output_parts.append("\nCategories Found:")
    for category in sorted(categories):
        category_issues = issues_by_category.get(category, [])
        output_parts.append(f"- {category.upper()}: {len(category_issues)} issues")
    
    return "\n".join(output_parts)


def _format_comparison_as_json(reviews: List[Dict[str, Any]], categories: Set[str], 
                             issues_by_category: Dict[str, List[Dict[str, Any]]], 
                             file_paths: Set[str]) -> str:
    """Format the comparison report as JSON.
    
    Args:
        reviews: List of review data dictionaries.
        categories: Set of feedback categories found across reviews.
        issues_by_category: Dictionary of issues grouped by category.
        file_paths: Set of file paths mentioned in the reviews.
        
    Returns:
        The formatted comparison as a JSON string.
    """
    import json
    
    comparison_data = {
        "reviews": [os.path.basename(review["file_path"]) for review in reviews],
        "categories": list(categories),
        "issues_by_category": {category: len(issues) for category, issues in issues_by_category.items()},
        "files_with_issues": list(file_paths),
        "detailed_issues": issues_by_category
    }
    
    return json.dumps(comparison_data, indent=2)


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
