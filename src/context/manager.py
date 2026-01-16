"""
Context Manager for tracking token usage and offloading context to files.
"""

import os
import json
from datetime import datetime
from typing import Optional
from google import genai
from google.genai import types

from ..config import (
    GEMINI_API_KEY,
    MODEL_NAME,
    TOKEN_THRESHOLD,
    MAX_CONTEXT_TOKENS,
    CONTEXT_ARCHIVE_DIR,
    THINKING_LEVEL,
)


class ContextManager:
    """
    Manages context window tracking and offloading for agents.
    
    When an agent's conversation history approaches the token limit,
    this manager archives the old context to a file and creates a 
    summary for the agent to reference.
    """
    
    def __init__(self, client: genai.Client):
        """
        Initialize the context manager.
        
        Args:
            client: Shared Gemini client instance
        """
        self.client = client
        os.makedirs(CONTEXT_ARCHIVE_DIR, exist_ok=True)
    
    def count_tokens(self, messages: list[dict]) -> int:
        """
        Count tokens in a list of messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Total token count
        """
        # Convert messages to text for counting
        text_content = "\n".join(
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in messages
        )
        
        try:
            response = self.client.models.count_tokens(
                model=MODEL_NAME,
                contents=text_content,
            )
            return response.total_tokens
        except Exception as e:
            # Fallback: rough estimate (4 chars per token)
            print(f"Warning: Token counting failed ({e}), using estimate")
            return len(text_content) // 4
    
    def should_offload(self, messages: list[dict]) -> bool:
        """
        Check if context should be offloaded based on token count.
        
        Args:
            messages: Current conversation history
            
        Returns:
            True if token count exceeds threshold
        """
        token_count = self.count_tokens(messages)
        return token_count > TOKEN_THRESHOLD
    
    def generate_summary(self, messages: list[dict], agent_name: str) -> str:
        """
        Generate a summary of the conversation history.
        
        Args:
            messages: Messages to summarize
            agent_name: Name of the agent for context
            
        Returns:
            Summary string
        """
        # Prepare the conversation for summarization
        conversation_text = "\n\n".join(
            f"[{msg.get('role', 'unknown').upper()}]\n{msg.get('content', '')}"
            for msg in messages
        )
        
        summary_prompt = f"""You are summarizing the work history of an agent named "{agent_name}" in a collaborative movie creation system.

Summarize the following conversation history, focusing on:
1. What drafts were worked on
2. Key decisions and changes made
3. Important feedback received
4. Current state of the story/work

Be concise but preserve critical details that the agent might need to reference.

CONVERSATION HISTORY:
{conversation_text}

SUMMARY:"""

        try:
            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=summary_prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
                    max_output_tokens=2000,
                ),
            )
            return response.text
        except Exception as e:
            # Fallback: simple extraction of key points
            print(f"Warning: Summary generation failed ({e}), using fallback")
            return f"[Auto-summary failed. Agent: {agent_name}. Messages archived: {len(messages)}]"
    
    def offload_context(
        self,
        messages: list[dict],
        agent_name: str,
        draft_num: int,
    ) -> tuple[str, str, str]:
        """
        Archive old context to a file and return a memory reminder.
        
        Args:
            messages: Full conversation history
            agent_name: Name of the agent
            draft_num: Current draft number
            
        Returns:
            Tuple of (archive_filepath, summary, memory_reminder)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{agent_name}_draft{draft_num:02d}_{timestamp}.txt"
        filepath = os.path.join(CONTEXT_ARCHIVE_DIR, filename)
        
        # Generate summary before archiving
        summary = self.generate_summary(messages, agent_name)
        
        # Archive the full conversation
        archive_content = {
            "agent_name": agent_name,
            "draft_num": draft_num,
            "timestamp": timestamp,
            "message_count": len(messages),
            "summary": summary,
            "messages": messages,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(archive_content, f, indent=2, ensure_ascii=False)
        
        # Create memory reminder for new context
        memory_reminder = f"""[MEMORY REMINDER]
Previous context has been archived to: {filepath}

Summary of prior work:
{summary}

If you need to reference specific details from earlier conversations, 
the full history is available in the archived file above.
---
"""
        
        print(f"  Context offloaded for {agent_name}: {len(messages)} messages archived")
        
        return filepath, summary, memory_reminder
    
    def load_archived_context(self, filepath: str) -> Optional[dict]:
        """
        Load archived context from a file.
        
        Args:
            filepath: Path to the archive file
            
        Returns:
            Archived context dict or None if not found
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load archived context ({e})")
            return None
    
    def get_context_stats(self, messages: list[dict]) -> dict:
        """
        Get statistics about current context usage.
        
        Args:
            messages: Current conversation history
            
        Returns:
            Dict with token count, percentage used, and threshold info
        """
        token_count = self.count_tokens(messages)
        percentage = (token_count / MAX_CONTEXT_TOKENS) * 100
        
        return {
            "token_count": token_count,
            "max_tokens": MAX_CONTEXT_TOKENS,
            "threshold": TOKEN_THRESHOLD,
            "percentage_used": round(percentage, 2),
            "should_offload": token_count > TOKEN_THRESHOLD,
        }

