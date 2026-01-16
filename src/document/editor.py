"""
Document Editor - Provides line-based editing operations on the working draft.
"""

import os
import re
from typing import Optional
from datetime import datetime


class DocumentEditor:
    """
    Manages a working document with line-based editing operations.
    
    Agents use this to make targeted edits rather than regenerating
    the entire document each time.
    """
    
    def __init__(self, filepath: str):
        """
        Initialize the document editor.
        
        Args:
            filepath: Path to the working document
        """
        self.filepath = filepath
        self.lines: list[str] = []
        self.edit_history: list[dict] = []
        
        # Load existing document or create empty
        if os.path.exists(filepath):
            self.load()
        else:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            self.lines = []
            self.save()
    
    def load(self) -> None:
        """Load the document from disk."""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            self.lines = content.split('\n')
    
    def save(self) -> None:
        """Save the document to disk."""
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.lines))
    
    def get_content(self) -> str:
        """Get the full document content."""
        return '\n'.join(self.lines)
    
    def get_line_count(self) -> int:
        """Get total number of lines."""
        return len(self.lines)
    
    def read_lines(self, start: int, end: int) -> str:
        """
        Read a range of lines (1-indexed, inclusive).
        
        Args:
            start: Starting line number (1-indexed)
            end: Ending line number (1-indexed, inclusive)
            
        Returns:
            Content of the specified lines with line numbers
        """
        start_idx = max(0, start - 1)
        end_idx = min(len(self.lines), end)
        
        result = []
        for i in range(start_idx, end_idx):
            result.append(f"{i + 1:4d}| {self.lines[i]}")
        
        return '\n'.join(result)
    
    def read_document_with_numbers(self) -> str:
        """Read full document with line numbers."""
        return self.read_lines(1, len(self.lines))
    
    def insert_lines(self, after_line: int, content: str, agent: str = "unknown") -> dict:
        """
        Insert new lines after a specific line.
        
        Args:
            after_line: Line number to insert after (0 = beginning, -1 = end)
            content: Content to insert (can be multi-line)
            agent: Name of agent making the edit
            
        Returns:
            Dict with operation result
        """
        new_lines = content.split('\n')
        
        if after_line == -1 or after_line >= len(self.lines):
            # Append to end
            insert_idx = len(self.lines)
        else:
            insert_idx = max(0, after_line)
        
        # Insert the lines
        for i, line in enumerate(new_lines):
            self.lines.insert(insert_idx + i, line)
        
        # Log the edit
        edit = {
            "operation": "insert",
            "agent": agent,
            "after_line": after_line,
            "lines_added": len(new_lines),
            "timestamp": datetime.now().isoformat(),
        }
        self.edit_history.append(edit)
        self.save()
        
        return {
            "success": True,
            "operation": "insert",
            "lines_added": len(new_lines),
            "starting_at_line": insert_idx + 1,
        }
    
    def delete_lines(self, start: int, end: int, agent: str = "unknown") -> dict:
        """
        Delete a range of lines (1-indexed, inclusive).
        
        Args:
            start: Starting line number (1-indexed)
            end: Ending line number (1-indexed, inclusive)
            agent: Name of agent making the edit
            
        Returns:
            Dict with operation result
        """
        start_idx = max(0, start - 1)
        end_idx = min(len(self.lines), end)
        
        deleted_content = self.lines[start_idx:end_idx]
        del self.lines[start_idx:end_idx]
        
        # Log the edit
        edit = {
            "operation": "delete",
            "agent": agent,
            "start_line": start,
            "end_line": end,
            "lines_deleted": len(deleted_content),
            "timestamp": datetime.now().isoformat(),
        }
        self.edit_history.append(edit)
        self.save()
        
        return {
            "success": True,
            "operation": "delete",
            "lines_deleted": len(deleted_content),
            "from_line": start,
            "to_line": end,
        }
    
    def replace_lines(self, start: int, end: int, content: str, agent: str = "unknown") -> dict:
        """
        Replace a range of lines with new content.
        
        Args:
            start: Starting line number (1-indexed)
            end: Ending line number (1-indexed, inclusive)
            content: New content to replace with
            agent: Name of agent making the edit
            
        Returns:
            Dict with operation result
        """
        start_idx = max(0, start - 1)
        end_idx = min(len(self.lines), end)
        
        old_lines = self.lines[start_idx:end_idx]
        new_lines = content.split('\n')
        
        # Replace the lines
        self.lines[start_idx:end_idx] = new_lines
        
        # Log the edit
        edit = {
            "operation": "replace",
            "agent": agent,
            "start_line": start,
            "end_line": end,
            "old_line_count": len(old_lines),
            "new_line_count": len(new_lines),
            "timestamp": datetime.now().isoformat(),
        }
        self.edit_history.append(edit)
        self.save()
        
        return {
            "success": True,
            "operation": "replace",
            "old_lines": len(old_lines),
            "new_lines": len(new_lines),
            "at_line": start,
        }
    
    def find_section(self, section_pattern: str) -> Optional[dict]:
        """
        Find a section by header pattern.
        
        Args:
            section_pattern: Regex pattern to match section header (e.g., "## SCENE 1")
            
        Returns:
            Dict with start_line, end_line, header, or None if not found
        """
        pattern = re.compile(section_pattern, re.IGNORECASE)
        
        for i, line in enumerate(self.lines):
            if pattern.search(line):
                # Found the section header
                start_line = i + 1  # 1-indexed
                
                # Find the end (next section header or end of document)
                end_line = len(self.lines)
                for j in range(i + 1, len(self.lines)):
                    # Check if this is another section header (## at start)
                    if self.lines[j].startswith('## ') or self.lines[j].startswith('---'):
                        end_line = j  # Don't include the next header
                        break
                
                return {
                    "found": True,
                    "header": line,
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": '\n'.join(self.lines[i:end_line]),
                }
        
        return {"found": False, "pattern": section_pattern}
    
    def find_all_sections(self) -> list[dict]:
        """
        Find all sections in the document.
        
        Returns:
            List of section info dicts
        """
        sections = []
        current_section = None
        
        for i, line in enumerate(self.lines):
            if line.startswith('## '):
                if current_section:
                    current_section["end_line"] = i
                    sections.append(current_section)
                
                current_section = {
                    "header": line,
                    "start_line": i + 1,
                    "end_line": None,
                }
        
        if current_section:
            current_section["end_line"] = len(self.lines)
            sections.append(current_section)
        
        return sections
    
    def insert_after_pattern(self, pattern: str, content: str, agent: str = "unknown") -> dict:
        """
        Insert content after the first line matching a pattern.
        
        Args:
            pattern: Regex pattern to find
            content: Content to insert after the matched line
            agent: Name of agent making the edit
            
        Returns:
            Dict with operation result
        """
        regex = re.compile(pattern, re.IGNORECASE)
        
        for i, line in enumerate(self.lines):
            if regex.search(line):
                return self.insert_lines(i + 1, content, agent)
        
        return {"success": False, "error": f"Pattern not found: {pattern}"}
    
    def clear(self) -> None:
        """Clear the document."""
        self.lines = []
        self.edit_history = []
        self.save()
    
    def set_content(self, content: str, agent: str = "unknown") -> dict:
        """
        Set the entire document content (used for initial creation).
        
        Args:
            content: Full document content
            agent: Name of agent making the edit
            
        Returns:
            Dict with operation result
        """
        self.lines = content.split('\n')
        
        edit = {
            "operation": "set_content",
            "agent": agent,
            "line_count": len(self.lines),
            "timestamp": datetime.now().isoformat(),
        }
        self.edit_history.append(edit)
        self.save()
        
        return {
            "success": True,
            "operation": "set_content",
            "line_count": len(self.lines),
        }
    
    def get_edit_history(self) -> list[dict]:
        """Get the edit history."""
        return self.edit_history


# Tool definitions for Gemini function calling
DOCUMENT_TOOLS = [
    {
        "name": "read_document",
        "description": "Read the entire working document with line numbers. Use this to see the current state of the draft.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "read_lines",
        "description": "Read a specific range of lines from the document. Lines are 1-indexed.",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {
                    "type": "integer",
                    "description": "Starting line number (1-indexed)",
                },
                "end": {
                    "type": "integer",
                    "description": "Ending line number (1-indexed, inclusive)",
                },
            },
            "required": ["start", "end"],
        },
    },
    {
        "name": "insert_lines",
        "description": "Insert new lines after a specific line number. Use after_line=0 to insert at the beginning, or after_line=-1 to append at the end.",
        "parameters": {
            "type": "object",
            "properties": {
                "after_line": {
                    "type": "integer",
                    "description": "Line number to insert after (0=beginning, -1=end)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to insert (can be multi-line)",
                },
            },
            "required": ["after_line", "content"],
        },
    },
    {
        "name": "delete_lines",
        "description": "Delete a range of lines from the document.",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {
                    "type": "integer",
                    "description": "Starting line number (1-indexed)",
                },
                "end": {
                    "type": "integer",
                    "description": "Ending line number (1-indexed, inclusive)",
                },
            },
            "required": ["start", "end"],
        },
    },
    {
        "name": "replace_lines",
        "description": "Replace a range of lines with new content.",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {
                    "type": "integer",
                    "description": "Starting line number (1-indexed)",
                },
                "end": {
                    "type": "integer",
                    "description": "Ending line number (1-indexed, inclusive)",
                },
                "content": {
                    "type": "string",
                    "description": "New content to replace the lines with",
                },
            },
            "required": ["start", "end", "content"],
        },
    },
    {
        "name": "find_section",
        "description": "Find a section by its header (e.g., 'SCENE 1', 'STORY OVERVIEW'). Returns the line range of that section.",
        "parameters": {
            "type": "object",
            "properties": {
                "section_name": {
                    "type": "string",
                    "description": "Name or pattern to search for in section headers",
                },
            },
            "required": ["section_name"],
        },
    },
    {
        "name": "insert_after_pattern",
        "description": "Insert content after the first line matching a pattern. Useful for adding [VISUAL] or [AUDIO] tags after specific narrative lines.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Text pattern to search for",
                },
                "content": {
                    "type": "string",
                    "description": "Content to insert after the matched line",
                },
            },
            "required": ["pattern", "content"],
        },
    },
    {
        "name": "editing_complete",
        "description": "Signal that you have finished all your edits to the document.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of edits made",
                },
            },
            "required": ["summary"],
        },
    },
]

