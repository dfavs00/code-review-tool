"""Git client interface for fetching and analyzing diffs between branches."""

from typing import Dict, List, Optional, Tuple
import os
from pathlib import Path
import git
from git import Repo


class GitClient:
    """Interface for interacting with Git repositories.
    
    This class provides methods to fetch diffs between branches and extract
    relevant information for code review.
    """
    
    def __init__(self, repo_path: Optional[str] = None) -> None:
        """Initialize the Git client with a repository path.
        
        Args:
            repo_path: Path to the Git repository. If None, uses the current directory.
        """
        # Use current directory if no path is provided
        self.repo_path = repo_path or os.getcwd()
        # Initialize the repository object
        self._repo: Optional[Repo] = None
    
    def _get_repo(self) -> Repo:
        """Get or initialize the Git repository object.
        
        Returns:
            The Git repository object.
            
        Raises:
            git.exc.InvalidGitRepositoryError: If the path is not a valid Git repository.
        """
        if self._repo is None:
            self._repo = Repo(self.repo_path)
        return self._repo
    
    def get_diff(self, target_branch: str, current_branch: Optional[str] = None) -> str:
        """Get the diff between the current branch and the target branch.
        
        Args:
            target_branch: The target branch to compare against.
            current_branch: The current branch. If None, uses the current HEAD.
            
        Returns:
            The diff as a string.
        """
        repo = self._get_repo()
        # Use current HEAD if no branch is specified
        current = current_branch or repo.active_branch.name
        
        # Get the diff between branches
        diff = repo.git.diff(target_branch, current)
        return diff
    
    def get_changed_files(self, target_branch: str, current_branch: Optional[str] = None) -> List[str]:
        """Get a list of files that have changed between branches.
        
        Args:
            target_branch: The target branch to compare against.
            current_branch: The current branch. If None, uses the current HEAD.
            
        Returns:
            A list of changed file paths.
        """
        repo = self._get_repo()
        # Use current HEAD if no branch is specified
        current = current_branch or repo.active_branch.name
        
        # Get the list of changed files
        changed_files = repo.git.diff('--name-only', target_branch, current).splitlines()
        return changed_files
    
    def get_file_content(self, file_path: str, branch: Optional[str] = None) -> str:
        """Get the content of a file from a specific branch.
        
        Args:
            file_path: Path to the file relative to the repository root.
            branch: The branch to get the file from. If None, uses the current HEAD.
            
        Returns:
            The content of the file as a string.
            
        Raises:
            FileNotFoundError: If the file doesn't exist in the specified branch.
        """
        repo = self._get_repo()
        # Use current HEAD if no branch is specified
        ref = branch or 'HEAD'
        
        try:
            # Get the file content from the specified branch
            content = repo.git.show(f'{ref}:{file_path}')
            return content
        except git.exc.GitCommandError:
            raise FileNotFoundError(f"File '{file_path}' not found in branch '{ref}'")
