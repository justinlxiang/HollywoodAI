"""
Writer Editor Agent - Creates and revises the narrative using document editing tools.
"""

from google import genai

from .editor_agent import EditorAgent
from ..context.manager import ContextManager


WRITER_EDITOR_PROMPT = """You are a master screenwriter editing a working draft document.

## Your Role:
- Create and refine narrative structure, scenes, and dialogue
- Make TARGETED edits - don't rewrite everything, just what needs changing
- Preserve existing [VISUAL] and [AUDIO] tags when editing (other agents added those)

## CRITICAL EDITING RULE - ALWAYS DELETE OLD CONTENT WHEN REVISING:
When you modify, improve, or revise ANY existing content:
- Use `replace_lines` to swap old content with new content (this deletes AND inserts in one operation)
- OR use `delete_lines` first, THEN `insert_lines` to add the replacement
- NEVER just insert new content below/above old content without deleting the original
- If you're improving a line, the OLD line must be REMOVED, not left in place

WRONG (creates duplicates):
  Line 50: "He walks slowly."
  → insert_lines(after_line=50, content="He strides purposefully.")
  Result: BOTH lines exist (BROKEN!)

CORRECT (replaces properly):
  Line 50: "He walks slowly."
  → replace_lines(start=50, end=50, content="He strides purposefully.")
  Result: Only the new line exists (CORRECT!)

## For FIRST DRAFT (empty document):
Use insert_lines with after_line=0 to create the initial story structure:
1. Title and metadata
2. STORY OVERVIEW section (logline, theme, arc, characters, emotional journey, goal)
3. SCENE sections with narrative, dialogue, and scene breaks
4. Production Notes at the end

## For REVISIONS:
1. First, read the document to understand current state
2. Use find_section to locate specific scenes
3. Make targeted edits using replace_lines or insert_lines
4. Only change what the feedback specifically addresses
5. PRESERVE all [VISUAL] and [AUDIO] tags unless they conflict with your changes

## PLOT HOLE PREVENTION:
Before any edit, ask yourself:
- "Why don't they just...?" - Is there an obvious solution being ignored?
- If a character forgets something, can another character tell them?
- Does the plot depend on characters NOT sharing obvious information?

## Document Format:
```
# [MOVIE TITLE]

**Genre:** [Genre]  
**Tone:** [Tone]  
**Estimated Runtime:** ~10 minutes  
**Draft:** [N] of [Total]

---

## STORY OVERVIEW
### Logline
### Theme
### Story Arc
### Characters
### Emotional Journey
### Goal

---

## SCENE 1: [Title]
**Location:** [Setting]
**Time:** [Time]

[Narrative and dialogue...]

---
```

Call editing_complete with a summary when done."""


class WriterEditorAgent(EditorAgent):
    """
    Writer agent that uses editing tools to create and revise the story.
    """
    
    def __init__(self, client: genai.Client, context_manager: ContextManager):
        super().__init__(
            name="Writer",
            system_prompt=WRITER_EDITOR_PROMPT,
            client=client,
            context_manager=context_manager,
        )
    
    def create_initial_draft(
        self,
        editor,
        user_prompt: str,
        research: str,
        draft_num: int,
        total_drafts: int,
    ) -> dict:
        """Create the initial draft from scratch."""
        task = f"""Create the FIRST DRAFT of a ~10 minute short film.

User Request: {user_prompt if user_prompt else "Create an original, compelling story. Surprise me with the genre and concept."}

{"Research Brief:" + chr(10) + research if research else ""}

Draft {draft_num} of {total_drafts}.

Important:
1. Start with a complete STORY OVERVIEW section
2. Create 4-8 scenes with clear narrative and dialogue
3. Leave room for [VISUAL] and [AUDIO] tags (don't add them yourself)
4. End with Production Notes (runtime estimates)
5. CHECK FOR PLOT HOLES before finalizing"""

        return self.call(editor, task, draft_num)
    
    def revise_draft(
        self,
        editor,
        feedback: str,
        draft_num: int,
        total_drafts: int,
    ) -> dict:
        """Revise the draft based on feedback."""
        task = f"""Revise the draft based on this feedback:

{feedback}

This is Draft {draft_num} of {total_drafts}.

Instructions:
1. Read the current document first
2. Address the MOST IMPORTANT issues from the feedback
3. Make TARGETED edits - don't rewrite sections that are working well
4. PRESERVE existing [VISUAL] and [AUDIO] tags
5. Update the Draft number in the metadata
6. CHECK FOR PLOT HOLES - especially any "why don't they just..." issues"""

        return self.call(editor, task, draft_num)

