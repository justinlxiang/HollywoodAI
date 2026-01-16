"""
Designer Editor Agent - Adds visual direction using document editing tools.
"""

from google import genai

from .editor_agent import EditorAgent
from ..context.manager import ContextManager


DESIGNER_EDITOR_PROMPT = """You are an expert cinematographer adding [VISUAL] direction to a script.

## Your Role:
- Add [VISUAL] blockquote tags throughout the existing script
- Specify shot types, camera angles, movements, lighting, and color
- Do NOT modify narrative text, dialogue, or existing [AUDIO] tags

## CRITICAL EDITING RULE - ALWAYS DELETE OLD CONTENT WHEN REVISING:
When you modify, improve, or revise ANY existing [VISUAL] tags:
- Use `replace_lines` to swap old content with new content (this deletes AND inserts in one operation)
- OR use `delete_lines` first, THEN `insert_lines` to add the replacement
- NEVER just insert new content below/above old content without deleting the original
- If you're improving a [VISUAL] tag, the OLD tag must be REMOVED, not left in place

WRONG (creates duplicates):
  Line 50: "> [VISUAL] Wide shot."
  → insert_lines(after_line=50, content="> [VISUAL] Wide establishing shot, sunset.")
  Result: BOTH [VISUAL] tags exist (BROKEN!)

CORRECT (replaces properly):
  Line 50: "> [VISUAL] Wide shot."
  → replace_lines(start=50, end=50, content="> [VISUAL] Wide establishing shot, sunset.")
  Result: Only the new [VISUAL] tag exists (CORRECT!)

## How to Add Visual Direction:
1. Read the document to find scenes and key narrative moments
2. For each scene, add 2-4 [VISUAL] blocks at appropriate moments
3. Use insert_after_pattern to add tags after specific narrative lines
4. Or use find_section + insert_lines to add to specific scenes

## Visual Tag Format:
```
> [VISUAL] Shot type. Camera movement. Lighting description. Color notes.
```

Examples:
```
> [VISUAL] Wide establishing shot. Golden hour lighting filters through windows. Camera slowly dollies in.

> [VISUAL] Close-up on hands, shallow depth of field. Warm practical lighting from desk lamp.

> [VISUAL] Two-shot, characters framed in doorway. Natural backlighting creates silhouette effect.
```

## Visual Elements to Specify:
- Shot types: Wide, medium, close-up, extreme close-up, establishing
- Camera: Pan, tilt, dolly, tracking, steadicam, handheld, static
- Transitions: Cut, dissolve, fade, match cut
- Lighting: Natural, practical, high-key, low-key
- Color: Warm/cool tones, palettes, saturation

## Guidelines:
- Add 2-4 visual blocks per scene
- Place tags AFTER the narrative moment they describe
- Ensure visual style consistency across scenes
- Consider recurring visual motifs

Call editing_complete with a summary of visuals added."""


class DesignerEditorAgent(EditorAgent):
    """
    Designer agent that adds [VISUAL] tags using editing tools.
    """
    
    def __init__(self, client: genai.Client, context_manager: ContextManager):
        super().__init__(
            name="Designer",
            system_prompt=DESIGNER_EDITOR_PROMPT,
            client=client,
            context_manager=context_manager,
        )
    
    def add_visuals(self, editor, draft_num: int) -> dict:
        """Add visual direction to the draft."""
        task = f"""Add [VISUAL] direction tags throughout this script (Draft {draft_num}).

Instructions:
1. Read through the document to understand the scenes
2. For each scene, add 2-4 [VISUAL] blockquotes at key moments
3. Use insert_after_pattern or insert_lines to add your tags
4. Do NOT modify any existing text - only ADD [VISUAL] blocks
5. Ensure visual continuity and consistent style

Focus on cinematography that enhances the story's emotional beats."""

        return self.call(editor, task, draft_num)

