"""Utility functions for the code review tool."""

from typing import Dict, List, Optional, Any, Union
import os
import json
from datetime import datetime
import re


def get_timestamp() -> str:
    """Get a formatted timestamp for file naming.
    
    Returns:
        A string in the format YYYYMMDD_HHMMSS.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_review_history(review_data: Dict[str, Any], output_dir: Optional[str] = None) -> str:
    """Save review data to a JSON history file.
    
    Args:
        review_data: Dictionary containing review data.
        output_dir: Directory to save the history file. Defaults to a 'history' folder
                    in the current directory.
    
    Returns:
        Path to the saved history file.
    """
    # Create history directory if it doesn't exist
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "history")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = get_timestamp()
    filename = f"review_history_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save the data
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(review_data, f, indent=2)
    
    return filepath


def parse_git_url(repo_url: str) -> Dict[str, str]:
    """Parse a Git repository URL into its components.
    
    Args:
        repo_url: The Git repository URL to parse.
    
    Returns:
        Dictionary containing the parsed components (protocol, host, user, repo).
    """
    # Common patterns for Git URLs
    patterns = [
        # SSH format: git@github.com:username/repo.git
        r"^git@([^:]+):([^/]+)/([^.]+)(?:\.git)?$",
        # HTTPS format: https://github.com/username/repo.git
        r"^(https?)://([^/]+)/([^/]+)/([^.]+)(?:\.git)?$"
    ]
    
    for pattern in patterns:
        match = re.match(pattern, repo_url)
        if match:
            if len(match.groups()) == 3:  # SSH format
                return {
                    "protocol": "ssh",
                    "host": match.group(1),
                    "user": match.group(2),
                    "repo": match.group(3)
                }
            else:  # HTTPS format
                return {
                    "protocol": match.group(1),
                    "host": match.group(2),
                    "user": match.group(3),
                    "repo": match.group(4)
                }
    
    # If no match found, return empty dict
    return {}


def count_lines_by_type(diff_text: str) -> Dict[str, int]:
    """Count the number of added, removed, and modified lines in a diff.
    
    Args:
        diff_text: The Git diff text to analyze.
    
    Returns:
        Dictionary with counts of added, removed, and modified lines.
    """
    added_lines = 0
    removed_lines = 0
    
    # Count lines starting with + or - (excluding diff headers which start with +++ or ---)
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added_lines += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed_lines += 1
    
    return {
        "added": added_lines,
        "removed": removed_lines,
        "total_changes": added_lines + removed_lines
    }
