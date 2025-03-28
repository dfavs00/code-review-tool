"""Parser for Git diffs to extract relevant code changes for review."""

from typing import Dict, List, Optional, Tuple, NamedTuple
import re


class FileDiff(NamedTuple):
    """Represents a diff for a single file."""
    file_path: str
    is_new_file: bool
    is_deleted: bool
    hunks: List[Dict[str, any]]


class DiffParser:
    """Parser for Git diffs to extract relevant code changes.
    
    This class provides methods to parse Git diff output and extract
    structured information about code changes for review.
    """
    
    def __init__(self) -> None:
        """Initialize the diff parser."""
        # Regex patterns for parsing diff output
        self._file_header_pattern = re.compile(r'^diff --git a/(.+) b/(.+)$')
        self._new_file_pattern = re.compile(r'^new file mode')
        self._deleted_file_pattern = re.compile(r'^deleted file mode')
        self._hunk_header_pattern = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
    
    def parse_diff(self, diff_text: str) -> List[FileDiff]:
        """Parse the Git diff text into structured file diffs.
        
        Args:
            diff_text: The Git diff output as a string.
            
        Returns:
            A list of FileDiff objects representing the changes in each file.
        """
        file_diffs: List[FileDiff] = []
        current_file: Optional[Dict[str, any]] = None
        current_hunk: Optional[Dict[str, any]] = None
        
        # Process each line of the diff
        for line in diff_text.splitlines():
            # Check for file header
            file_match = self._file_header_pattern.match(line)
            if file_match:
                # If we were processing a file, add it to the result
                if current_file:
                    file_diffs.append(FileDiff(
                        file_path=current_file['path'],
                        is_new_file=current_file['is_new'],
                        is_deleted=current_file['is_deleted'],
                        hunks=current_file['hunks']
                    ))
                
                # Start a new file diff
                current_file = {
                    'path': file_match.group(1),  # Use the path from the 'a/' side
                    'is_new': False,
                    'is_deleted': False,
                    'hunks': []
                }
                current_hunk = None
                continue
            
            # Skip if we're not processing a file yet
            if not current_file:
                continue
            
            # Check for new file indicator
            if self._new_file_pattern.match(line):
                current_file['is_new'] = True
                continue
            
            # Check for deleted file indicator
            if self._deleted_file_pattern.match(line):
                current_file['is_deleted'] = True
                continue
            
            # Check for hunk header
            hunk_match = self._hunk_header_pattern.match(line)
            if hunk_match:
                # Start a new hunk
                current_hunk = {
                    'old_start': int(hunk_match.group(1)),
                    'old_count': int(hunk_match.group(2) or 1),
                    'new_start': int(hunk_match.group(3)),
                    'new_count': int(hunk_match.group(4) or 1),
                    'lines': []
                }
                current_file['hunks'].append(current_hunk)
                continue
            
            # Skip if we're not processing a hunk yet
            if not current_hunk:
                continue
            
            # Add the line to the current hunk
            current_hunk['lines'].append(line)
        
        # Add the last file if there is one
        if current_file:
            file_diffs.append(FileDiff(
                file_path=current_file['path'],
                is_new_file=current_file['is_new'],
                is_deleted=current_file['is_deleted'],
                hunks=current_file['hunks']
            ))
        
        return file_diffs
    
    def extract_code_context(self, file_diffs: List[FileDiff], context_lines: int = 3) -> Dict[str, Dict[str, any]]:
        """Extract code context from file diffs for review.
        
        This function extracts the relevant code changes and surrounding context
        from the file diffs to provide better context for the LLM review.
        
        Args:
            file_diffs: List of FileDiff objects.
            context_lines: Number of context lines to include around changes.
            
        Returns:
            A dictionary mapping file paths to their code context information.
        """
        code_context: Dict[str, Dict[str, any]] = {}
        
        for file_diff in file_diffs:
            # Skip deleted files as they don't need review
            if file_diff.is_deleted:
                continue
            
            # Initialize context for this file
            file_context = {
                'is_new_file': file_diff.is_new_file,
                'changes': []
            }
            
            # Process each hunk to extract changes with context
            for hunk in file_diff.hunks:
                # Extract the changed lines with context
                change_lines = self._extract_change_with_context(hunk, context_lines)
                if change_lines:
                    file_context['changes'].append({
                        'start_line': hunk['new_start'],
                        'lines': change_lines
                    })
            
            # Add the file context to the result if it has changes
            if file_context['changes']:
                code_context[file_diff.file_path] = file_context
        
        return code_context
    
    def _extract_change_with_context(self, hunk: Dict[str, any], context_lines: int) -> List[str]:
        """Extract changed lines with surrounding context from a hunk.
        
        Args:
            hunk: The hunk dictionary containing the lines.
            context_lines: Number of context lines to include.
            
        Returns:
            A list of lines representing the changes with context.
        """
        # Filter out lines that start with '---' or '+++' (diff metadata)
        code_lines = [line for line in hunk['lines'] if not (line.startswith('---') or line.startswith('+++'))]
        
        # If there are no meaningful lines, return empty list
        if not code_lines:
            return []
        
        # Return all lines for small hunks
        return code_lines
