"""Process and format LLM feedback for code reviews."""

from typing import Dict, List, Optional, Any, NamedTuple
import re
from enum import Enum


class FeedbackCategory(Enum):
    """Categories for code review feedback."""
    GENERAL = "general"
    BEST_PRACTICE = "best_practice"
    SECURITY = "security"
    PERFORMANCE = "performance"
    READABILITY = "readability"
    BUG = "bug"
    SUGGESTION = "suggestion"


class FeedbackItem(NamedTuple):
    """Represents a single feedback item in a code review."""
    category: FeedbackCategory
    file_path: Optional[str]
    line_number: Optional[int]
    message: str
    severity: str  # 'high', 'medium', 'low'


class FeedbackProcessor:
    """Process and structure LLM-generated feedback for code reviews.
    
    This class provides methods to parse, categorize, and format the raw
    feedback from LLMs into structured feedback items.
    """
    
    def __init__(self) -> None:
        """Initialize the feedback processor."""
        # Regex patterns for extracting structured information from LLM output
        self._file_pattern = re.compile(r'\b(?:in|file|for)\s+(["\'])(.*?)\1', re.IGNORECASE)
        self._line_pattern = re.compile(r'\b(?:line|at line)\s+(\d+)', re.IGNORECASE)
        self._severity_words = {
            'high': ['critical', 'severe', 'major', 'important', 'significant'],
            'medium': ['moderate', 'consider', 'should', 'recommend'],
            'low': ['minor', 'trivial', 'style', 'nit', 'suggestion']
        }
    
    def process_feedback(self, raw_feedback: str) -> List[FeedbackItem]:
        """Process raw LLM feedback into structured feedback items.
        
        Args:
            raw_feedback: The raw feedback text from the LLM.
            
        Returns:
            A list of structured FeedbackItem objects.
        """
        # Split the feedback into paragraphs
        paragraphs = [p.strip() for p in raw_feedback.split('\n\n') if p.strip()]
        
        # Process each paragraph into a feedback item
        feedback_items: List[FeedbackItem] = []
        for paragraph in paragraphs:
            item = self._process_paragraph(paragraph)
            if item:
                feedback_items.append(item)
        
        return feedback_items
    
    def _process_paragraph(self, paragraph: str) -> Optional[FeedbackItem]:
        """Process a single paragraph into a feedback item.
        
        Args:
            paragraph: A paragraph of feedback text.
            
        Returns:
            A FeedbackItem if the paragraph contains valid feedback, None otherwise.
        """
        # Skip empty paragraphs or section headers
        if not paragraph or len(paragraph) < 10 or paragraph.endswith(':'):
            return None
        
        # Extract file path if present
        file_match = self._file_pattern.search(paragraph)
        file_path = file_match.group(2) if file_match else None
        
        # Extract line number if present
        line_match = self._line_pattern.search(paragraph)
        line_number = int(line_match.group(1)) if line_match else None
        
        # Determine the category based on content
        category = self._determine_category(paragraph)
        
        # Determine the severity based on content
        severity = self._determine_severity(paragraph)
        
        # Create and return the feedback item
        return FeedbackItem(
            category=category,
            file_path=file_path,
            line_number=line_number,
            message=paragraph,
            severity=severity
        )
    
    def _determine_category(self, text: str) -> FeedbackCategory:
        """Determine the feedback category based on the text content.
        
        Args:
            text: The feedback text.
            
        Returns:
            The determined FeedbackCategory.
        """
        text_lower = text.lower()
        
        # Check for security issues
        if any(word in text_lower for word in ['security', 'vulnerability', 'exploit', 'attack', 'unsafe']):
            return FeedbackCategory.SECURITY
        
        # Check for performance issues
        if any(word in text_lower for word in ['performance', 'slow', 'efficient', 'optimization', 'speed']):
            return FeedbackCategory.PERFORMANCE
        
        # Check for bugs
        if any(word in text_lower for word in ['bug', 'error', 'exception', 'crash', 'incorrect', 'fix']):
            return FeedbackCategory.BUG
        
        # Check for readability issues
        if any(word in text_lower for word in ['readability', 'clarity', 'confusing', 'naming', 'comment']):
            return FeedbackCategory.READABILITY
        
        # Check for best practices
        if any(word in text_lower for word in ['practice', 'convention', 'standard', 'pattern', 'approach']):
            return FeedbackCategory.BEST_PRACTICE
        
        # Check for suggestions
        if any(word in text_lower for word in ['suggest', 'recommend', 'consider', 'might', 'could']):
            return FeedbackCategory.SUGGESTION
        
        # Default to general feedback
        return FeedbackCategory.GENERAL
    
    def _determine_severity(self, text: str) -> str:
        """Determine the severity of the feedback based on the text content.
        
        Args:
            text: The feedback text.
            
        Returns:
            The severity level as a string ('high', 'medium', or 'low').
        """
        text_lower = text.lower()
        
        # Check for high severity indicators
        if any(word in text_lower for word in self._severity_words['high']):
            return 'high'
        
        # Check for low severity indicators
        if any(word in text_lower for word in self._severity_words['low']):
            return 'low'
        
        # Default to medium severity
        return 'medium'
    
    def format_feedback(self, feedback_items: List[FeedbackItem], format_type: str = 'text') -> str:
        """Format the feedback items for output.
        
        Args:
            feedback_items: List of FeedbackItem objects.
            format_type: The output format ('text', 'markdown', or 'json').
            
        Returns:
            The formatted feedback as a string.
            
        Raises:
            ValueError: If the format type is not supported.
        """
        if format_type == 'text':
            return self._format_as_text(feedback_items)
        elif format_type == 'markdown':
            return self._format_as_markdown(feedback_items)
        elif format_type == 'json':
            return self._format_as_json(feedback_items)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def _format_as_text(self, feedback_items: List[FeedbackItem]) -> str:
        """Format feedback items as plain text.
        
        Args:
            feedback_items: List of FeedbackItem objects.
            
        Returns:
            The formatted feedback as plain text.
        """
        if not feedback_items:
            return "No feedback items found."
        
        # Group feedback items by category
        items_by_category: Dict[FeedbackCategory, List[FeedbackItem]] = {}
        for item in feedback_items:
            if item.category not in items_by_category:
                items_by_category[item.category] = []
            items_by_category[item.category].append(item)
        
        # Format the output
        output_parts = ["CODE REVIEW FEEDBACK\n===================\n"]
        
        # Add a summary of feedback items by category
        output_parts.append("Summary:")
        for category, items in items_by_category.items():
            output_parts.append(f"- {category.value.title()}: {len(items)} items")
        
        # Add detailed feedback by category
        for category, items in items_by_category.items():
            output_parts.append(f"\n{category.value.upper()}\n{'-' * len(category.value)}")
            
            for item in items:
                location = ""
                if item.file_path:
                    location += f"File: {item.file_path}"
                if item.line_number:
                    location += f", Line: {item.line_number}"
                
                if location:
                    output_parts.append(f"[{item.severity.upper()}] {location}")
                else:
                    output_parts.append(f"[{item.severity.upper()}]")
                
                output_parts.append(item.message)
                output_parts.append("")
        
        return "\n".join(output_parts)
    
    def _format_as_markdown(self, feedback_items: List[FeedbackItem]) -> str:
        """Format feedback items as markdown.
        
        Args:
            feedback_items: List of FeedbackItem objects.
            
        Returns:
            The formatted feedback as markdown.
        """
        if not feedback_items:
            return "# Code Review Feedback\n\nNo feedback items found."
        
        # Group feedback items by category
        items_by_category: Dict[FeedbackCategory, List[FeedbackItem]] = {}
        for item in feedback_items:
            if item.category not in items_by_category:
                items_by_category[item.category] = []
            items_by_category[item.category].append(item)
        
        # Format the output
        output_parts = ["# Code Review Feedback\n"]
        
        # Add a summary of feedback items by category
        output_parts.append("## Summary")
        for category, items in items_by_category.items():
            output_parts.append(f"- **{category.value.title()}**: {len(items)} items")
        
        # Add detailed feedback by category
        for category, items in items_by_category.items():
            output_parts.append(f"\n## {category.value.title()}")
            
            # Group items by file path for better organization
            items_by_file: Dict[str, List[FeedbackItem]] = {}
            general_items: List[FeedbackItem] = []
            
            for item in items:
                if item.file_path:
                    file_path = item.file_path
                    if file_path not in items_by_file:
                        items_by_file[file_path] = []
                    items_by_file[file_path].append(item)
                else:
                    general_items.append(item)
            
            # First add file-specific feedback
            for file_path, file_items in items_by_file.items():
                output_parts.append(f"### File: `{file_path}`")
                
                for item in file_items:
                    severity_emoji = {
                        'high': '🔴',
                        'medium': '🟠',
                        'low': '🟢'
                    }.get(item.severity, '⚪')
                    
                    # Add location information if available
                    if item.line_number:
                        output_parts.append(f"#### {severity_emoji} Line {item.line_number}")
                    else:
                        output_parts.append(f"#### {severity_emoji} Issue")
                    
                    output_parts.append(item.message)
                    output_parts.append("")
            
            # Then add general feedback for this category
            if general_items:
                if items_by_file:  # Add a separator if we already added file-specific feedback
                    output_parts.append("### General Feedback")
                
                for item in general_items:
                    severity_emoji = {
                        'high': '🔴',
                        'medium': '🟠',
                        'low': '🟢'
                    }.get(item.severity, '⚪')
                    
                    # For general feedback, don't add redundant headers
                    # Just use bullet points with emoji indicators
                    output_parts.append(f"**{severity_emoji} {item.message.splitlines()[0] if item.message.splitlines() else 'Feedback'}**")
                    
                    # Add the rest of the message content if it's multiline
                    if len(item.message.splitlines()) > 1:
                        output_parts.append("")
                        output_parts.append("\n".join(item.message.splitlines()[1:]))
                    
                    output_parts.append("")
        
        return "\n".join(output_parts)
    
    def _format_as_json(self, feedback_items: List[FeedbackItem]) -> str:
        """Format feedback items as JSON.
        
        Args:
            feedback_items: List of FeedbackItem objects.
            
        Returns:
            The formatted feedback as a JSON string.
        """
        import json
        
        # Convert feedback items to dictionaries
        items_as_dicts = [
            {
                'category': item.category.value,
                'file_path': item.file_path,
                'line_number': item.line_number,
                'message': item.message,
                'severity': item.severity
            }
            for item in feedback_items
        ]
        
        # Create a structured output
        output = {
            'summary': {
                'total_items': len(feedback_items),
                'categories': {}
            },
            'items': items_as_dicts
        }
        
        # Add category counts to the summary
        for item in feedback_items:
            category = item.category.value
            if category not in output['summary']['categories']:
                output['summary']['categories'][category] = 0
            output['summary']['categories'][category] += 1
        
        # Return the JSON string with indentation for readability
        return json.dumps(output, indent=2)
