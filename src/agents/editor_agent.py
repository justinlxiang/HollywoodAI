"""
Editor Agent - Base class for agents that edit the working document using tools.
"""

import json
from typing import Optional
from google import genai
from google.genai import types

from ..config import MODEL_NAME, THINKING_LEVEL
from ..context.manager import ContextManager
from ..document.editor import DocumentEditor, DOCUMENT_TOOLS


class EditorAgent:
    """
    Base class for agents that use tool calling to edit a shared document.
    
    Instead of generating the full document each time, these agents
    make targeted edits using document editing tools.
    
    Context Management:
    - Tracks conversation history across calls for each agent
    - Monitors token usage and offloads context when threshold is reached
    - Prepends memory reminders after context offload
    """
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        client: genai.Client,
        context_manager: ContextManager,
    ):
        """
        Initialize the editor agent.
        
        Args:
            name: Unique identifier for this agent
            system_prompt: The system prompt defining agent behavior
            client: Shared Gemini client instance
            context_manager: Shared context manager for token tracking
        """
        self.name = name
        self.system_prompt = system_prompt
        self.client = client
        self.context_manager = context_manager
        self.current_draft: int = 0
        
        # Conversation history for context tracking
        self.conversation_history: list[dict] = []
        self.memory_reminder: Optional[str] = None
        
        # Build tool declarations for Gemini
        self.tools = self._build_tools()
    
    def _build_tools(self) -> list[types.Tool]:
        """Build Gemini tool declarations from DOCUMENT_TOOLS."""
        function_declarations = []
        
        for tool in DOCUMENT_TOOLS:
            func_decl = types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=tool["parameters"],
            )
            function_declarations.append(func_decl)
        
        return [types.Tool(function_declarations=function_declarations)]
    
    def _execute_tool(self, tool_name: str, args: dict, editor: DocumentEditor) -> str:
        """
        Execute a tool call and return the result.
        
        Args:
            tool_name: Name of the tool to execute
            args: Arguments for the tool
            editor: DocumentEditor instance
            
        Returns:
            String result of the tool execution
        """
        try:
            if tool_name == "read_document":
                content = editor.read_document_with_numbers()
                return f"Document ({editor.get_line_count()} lines):\n{content}"
            
            elif tool_name == "read_lines":
                content = editor.read_lines(args["start"], args["end"])
                return f"Lines {args['start']}-{args['end']}:\n{content}"
            
            elif tool_name == "insert_lines":
                result = editor.insert_lines(
                    args["after_line"],
                    args["content"],
                    agent=self.name,
                )
                return json.dumps(result)
            
            elif tool_name == "delete_lines":
                result = editor.delete_lines(
                    args["start"],
                    args["end"],
                    agent=self.name,
                )
                return json.dumps(result)
            
            elif tool_name == "replace_lines":
                result = editor.replace_lines(
                    args["start"],
                    args["end"],
                    args["content"],
                    agent=self.name,
                )
                return json.dumps(result)
            
            elif tool_name == "find_section":
                result = editor.find_section(args["section_name"])
                return json.dumps(result)
            
            elif tool_name == "insert_after_pattern":
                result = editor.insert_after_pattern(
                    args["pattern"],
                    args["content"],
                    agent=self.name,
                )
                return json.dumps(result)
            
            elif tool_name == "editing_complete":
                return f"EDITING_COMPLETE: {args.get('summary', 'No summary provided')}"
            
            else:
                return f"Unknown tool: {tool_name}"
                
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def _check_and_manage_context(self, draft_num: int) -> None:
        """
        Check context usage and offload if necessary.
        
        Args:
            draft_num: Current draft number for archive naming
        """
        if not self.conversation_history:
            return
        
        # Check if we should offload
        if self.context_manager.should_offload(self.conversation_history):
            stats = self.context_manager.get_context_stats(self.conversation_history)
            print(f"  [{self.name}] Context threshold reached ({stats['percentage_used']:.1f}% used)")
            
            # Offload context
            filepath, summary, memory_reminder = self.context_manager.offload_context(
                self.conversation_history,
                self.name,
                draft_num,
            )
            
            # Store memory reminder for next message
            self.memory_reminder = memory_reminder
            
            # Clear history after offload
            self.conversation_history = []
            print(f"  [{self.name}] Context archived to: {filepath}")
    
    def _add_to_history(self, role: str, content: str) -> None:
        """
        Add a message to conversation history.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
        """
        self.conversation_history.append({
            "role": role,
            "content": content,
        })
    
    def get_context_stats(self) -> dict:
        """Get current context statistics for this agent."""
        return self.context_manager.get_context_stats(self.conversation_history)
    
    def clear_history(self) -> None:
        """Clear conversation history (useful between major phases)."""
        self.conversation_history = []
        self.memory_reminder = None
    
    def call(
        self,
        editor: DocumentEditor,
        task_prompt: str,
        draft_num: int = 0,
        max_iterations: int = 20,
    ) -> dict:
        """
        Call the agent to perform edits on the document.
        
        Args:
            editor: DocumentEditor instance for the working document
            task_prompt: Description of what the agent should do
            draft_num: Current draft number
            max_iterations: Maximum tool call iterations
            
        Returns:
            Dict with results and edit summary
        """
        self.current_draft = draft_num
        
        # Check if context needs to be offloaded before this call
        self._check_and_manage_context(draft_num)
        
        # Always provide the full document so agents see what others changed
        doc_content = editor.read_document_with_numbers()
        line_count = editor.get_line_count()
        
        if line_count == 0:
            initial_context = "The document is currently EMPTY. You need to create the initial content."
        else:
            initial_context = f"""## CURRENT DOCUMENT STATE ({line_count} lines)

{doc_content}

---
END OF DOCUMENT"""
        
        # Prepend memory reminder if context was previously offloaded
        memory_prefix = ""
        if self.memory_reminder:
            memory_prefix = f"{self.memory_reminder}\n\n"
            print(f"  [{self.name}] Including memory reminder from previous context")
        
        user_message = f"""{memory_prefix}{task_prompt}

{initial_context}

Use the editing tools to make your changes. Call editing_complete when done."""

        # Track this user message in history
        self._add_to_history("user", user_message)

        # Use a chat session for multi-turn function calling
        chat = self.client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
                tools=self.tools,
            ),
        )
        
        edit_summary = []
        iterations = 0
        
        # Log context stats
        stats = self.get_context_stats()
        print(f"\n  [{self.name}] INPUT:")
        print(f"  Task: {task_prompt[:150]}...")
        print(f"  Document: {line_count} lines (full content provided to agent)")
        print(f"  Context: {stats['token_count']} tokens ({stats['percentage_used']:.1f}% of max)")
        print(f"  [{self.name}] Starting document editing...")
        
        # Send initial message
        response = chat.send_message(user_message)
        
        while iterations < max_iterations:
            iterations += 1
            
            # Check for function calls
            has_function_call = False
            function_responses = []
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    has_function_call = True
                    fc = part.function_call
                    
                    # Execute the tool
                    result = self._execute_tool(fc.name, dict(fc.args), editor)
                    
                    # Check if editing is complete
                    if fc.name == "editing_complete":
                        summary = fc.args.get("summary", "Edits complete")
                        edit_summary.append(summary)
                        print(f"  [{self.name}] {summary}")
                        
                        # Track assistant response in history
                        self._add_to_history("assistant", f"[Completed editing] {summary}")
                        
                        # Clear memory reminder after successful use
                        self.memory_reminder = None
                        
                        result_dict = {
                            "success": True,
                            "agent": self.name,
                            "draft_num": draft_num,
                            "iterations": iterations,
                            "edit_summary": edit_summary,
                            "context_stats": self.get_context_stats(),
                        }
                        print(f"\n  [{self.name}] OUTPUT:")
                        print(f"  {result_dict}")
                        return result_dict
                    
                    # Log non-read operations
                    if fc.name not in ["read_document", "read_lines", "find_section"]:
                        print(f"  [{self.name}] {fc.name}: {dict(fc.args)}")
                        edit_summary.append(f"{fc.name}")
                    
                    # Build function response
                    function_responses.append(
                        types.FunctionResponse(
                            name=fc.name,
                            response={"result": result},
                        )
                    )
            
            if not has_function_call:
                # Model finished without calling editing_complete
                text_response = response.text if response.text else "No response"
                print(f"  [{self.name}] Finished: {text_response[:100]}...")
                
                # Track assistant response in history
                self._add_to_history("assistant", text_response)
                
                # Clear memory reminder after successful use
                self.memory_reminder = None
                
                result_dict = {
                    "success": True,
                    "agent": self.name,
                    "draft_num": draft_num,
                    "iterations": iterations,
                    "edit_summary": edit_summary,
                    "final_message": text_response,
                    "context_stats": self.get_context_stats(),
                }
                print(f"\n  [{self.name}] OUTPUT:")
                print(f"  {result_dict}")
                return result_dict
            
            # Send function responses back to continue the conversation
            # Convert FunctionResponse objects to Part objects
            parts = [types.Part(function_response=fr) for fr in function_responses]
            response = chat.send_message(parts)
        
        print(f"  [{self.name}] Max iterations reached")
        
        # Track in history even on failure
        self._add_to_history("assistant", f"[Max iterations reached] Edits: {edit_summary}")
        
        result_dict = {
            "success": False,
            "agent": self.name,
            "draft_num": draft_num,
            "iterations": iterations,
            "edit_summary": edit_summary,
            "error": "Max iterations reached",
            "context_stats": self.get_context_stats(),
        }
        print(f"\n  [{self.name}] OUTPUT:")
        print(f"  {result_dict}")
        return result_dict
