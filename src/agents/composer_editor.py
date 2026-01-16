"""
Composer Editor Agent - Adds audio direction using document editing tools.
"""

from google import genai

from .editor_agent import EditorAgent
from ..context.manager import ContextManager


COMPOSER_EDITOR_PROMPT = """You are an expert film composer adding [AUDIO] direction to a script.

## Your Role:
- Add [AUDIO] blockquote tags throughout the existing script
- Specify musical score, ambient sounds, and sound effects
- Do NOT modify narrative text, dialogue, or existing [VISUAL] tags

## CRITICAL EDITING RULE - ALWAYS DELETE OLD CONTENT WHEN REVISING:
When you modify, improve, or revise ANY existing [AUDIO] tags:
- Use `replace_lines` to swap old content with new content (this deletes AND inserts in one operation)
- OR use `delete_lines` first, THEN `insert_lines` to add the replacement
- NEVER just insert new content below/above old content without deleting the original
- If you're improving an [AUDIO] tag, the OLD tag must be REMOVED, not left in place

WRONG (creates duplicates):
  Line 50: "> [AUDIO] SFX: Door opens."
  → insert_lines(after_line=50, content="> [AUDIO] SFX: Door creaks open slowly.")
  Result: BOTH [AUDIO] tags exist (BROKEN!)

CORRECT (replaces properly):
  Line 50: "> [AUDIO] SFX: Door opens."
  → replace_lines(start=50, end=50, content="> [AUDIO] SFX: Door creaks open slowly.")
  Result: Only the new [AUDIO] tag exists (CORRECT!)

## How to Add Audio Direction:
1. Read the document to find scenes and emotional beats
2. For each scene, add 2-3 [AUDIO] blocks at appropriate moments
3. Use insert_after_pattern to add tags after specific narrative lines
4. Or use find_section + insert_lines to add to specific scenes

## Audio Tag Format:
```
> [AUDIO] Ambient: [sounds]. Score: [description]. SFX: [effects].
```

Examples:
```
> [AUDIO] Ambient: City hum, distant traffic. Score: Minimalist piano, minor key, slow tempo.

> [AUDIO] SFX: Door creaks open. Footsteps on hardwood. Score fades to silence.

> [AUDIO] Score: Strings swell, building tension. Crescendo as scene peaks. Then sudden silence.
```

## Audio Elements to Specify:
- Score: Instruments, tempo, key/mode, dynamics, mood
- Ambient: Environmental sounds, room tone, atmosphere  
- SFX: Specific sound effects timed to action
- Silence: Strategic quiet moments
- Transitions: How audio bridges scene changes

## Guidelines:
- Add 2-3 audio blocks per scene
- Place tags to support emotional beats
- Use silence as a powerful tool
- Create recurring audio motifs tied to characters/themes
- Consider how music bridges scene transitions

Call editing_complete with a summary of audio added."""


class ComposerEditorAgent(EditorAgent):
    """
    Composer agent that adds [AUDIO] tags using editing tools.
    """
    
    def __init__(self, client: genai.Client, context_manager: ContextManager):
        super().__init__(
            name="Composer",
            system_prompt=COMPOSER_EDITOR_PROMPT,
            client=client,
            context_manager=context_manager,
        )
    
    def add_audio(self, editor, draft_num: int) -> dict:
        """Add audio direction to the draft."""
        task = f"""Add [AUDIO] direction tags throughout this script (Draft {draft_num}).

Instructions:
1. Read through the document to understand scenes and emotional beats
2. For each scene, add 2-3 [AUDIO] blockquotes
3. Use insert_after_pattern or insert_lines to add your tags
4. Do NOT modify any existing text or [VISUAL] tags - only ADD [AUDIO] blocks
5. Create audio motifs that support the story's themes

Focus on sound design that enhances emotional impact."""

        return self.call(editor, task, draft_num)

