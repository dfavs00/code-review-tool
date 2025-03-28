"""Example usage of the AI Code Review Tool."""

import os
import sys
from typing import Dict, Any

# Add the project directory to the path to import the package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code_review_tool.git_client import GitClient
from code_review_tool.diff_parser import DiffParser
from code_review_tool.llm_integration import get_llm_client
from code_review_tool.feedback_processor import FeedbackProcessor


def run_example_review(target_branch: str = "main") -> None:
    """Run an example code review.
    
    Args:
        target_branch: The target branch to compare against.
    """
    # Step 1: Initialize components
    git_client = GitClient()  # Uses current directory
    diff_parser = DiffParser()
    feedback_processor = FeedbackProcessor()
    
    # Step 2: Get the diff between branches
    print(f"Fetching diff between '{target_branch}' and current branch...")
    diff = git_client.get_diff(target_branch)
    
    # Step 3: Parse the diff
    print("Parsing code changes...")
    file_diffs = diff_parser.parse_diff(diff)
    
    # Step 4: Extract code context
    code_context = diff_parser.extract_code_context(file_diffs, context_lines=3)
    
    # Check if there are any changes to review
    if not code_context:
        print("No code changes found to review.")
        return
    
    # Step 5: Get the LLM client (requires API key in environment variable)
    print("Using OpenAI for code review...")
    try:
        llm_client = get_llm_client("openai")
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure to set the OPENAI_API_KEY environment variable.")
        return
    
    # Step 6: Generate the review
    print("Generating code review...")
    raw_feedback = llm_client.generate_review(code_context)
    
    # Step 7: Process the feedback
    print("Processing feedback...")
    feedback_items = feedback_processor.process_feedback(raw_feedback)
    
    # Step 8: Format the feedback as markdown
    formatted_feedback = feedback_processor.format_feedback(feedback_items, "markdown")
    
    # Step 9: Save the feedback to a file
    output_file = "code_review_results.md"
    with open(output_file, "w") as f:
        f.write(formatted_feedback)
    
    print(f"Review saved to {output_file}")


def print_usage_instructions() -> None:
    """Print instructions for using the example script."""
    print("\nUsage Instructions:")
    print("------------------")
    print("1. Make sure you're in a Git repository")
    print("2. Set your OpenAI API key as an environment variable:")
    print("   - Windows: set OPENAI_API_KEY=your_api_key_here")
    print("   - Linux/Mac: export OPENAI_API_KEY=your_api_key_here")
    print("3. Run this script with the target branch to compare against:")
    print("   python example_usage.py main")
    print("\nThe review results will be saved to 'code_review_results.md'")


if __name__ == "__main__":
    # Print a welcome message
    print("AI Code Review Tool - Example Usage")
    print("===================================")
    
    # Get the target branch from command line arguments or use default
    target_branch = sys.argv[1] if len(sys.argv) > 1 else "main"
    
    # Run the example review
    run_example_review(target_branch)
    
    # Print usage instructions
    print_usage_instructions()
