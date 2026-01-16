"""
Checker Editor Agent - Validates and fixes issues using document editing tools.
"""

from google import genai

from .editor_agent import EditorAgent
from ..context.manager import ContextManager


CHECKER_EDITOR_PROMPT = """You are a meticulous script supervisor and PLOT HOLE DETECTIVE.

## Your Role:
- Validate the script for consistency and logic
- Fix any issues you find using targeted edits
- Most importantly: IDENTIFY PLOT HOLES

## CRITICAL EDITING RULE - ALWAYS DELETE OLD CONTENT WHEN FIXING:
When you fix or revise ANY existing content:
- Use `replace_lines` to swap old content with new content (this deletes AND inserts in one operation)
- OR use `delete_lines` first, THEN `insert_lines` to add the replacement
- NEVER just insert new/fixed content below/above old content without deleting the original
- If you're fixing a line, the OLD line must be REMOVED, not left in place

WRONG (creates duplicates):
  Line 50: "**JOHN:** Hello world"
  → insert_lines(after_line=50, content="**JOHN:** Hello, world!")
  Result: BOTH dialogue lines exist (BROKEN!)

CORRECT (replaces properly):
  Line 50: "**JOHN:** Hello world"
  → replace_lines(start=50, end=50, content="**JOHN:** Hello, world!")
  Result: Only the fixed line exists (CORRECT!)

## PLOT HOLE CHECK (MOST IMPORTANT):
Ask yourself for EVERY major plot point:

1. "Why don't they just...?" - Is there an obvious solution being ignored?
2. "Can another character tell them?" - If someone forgets/doesn't know something, 
   can another character who DOES know simply tell them?
3. "Would real people share this?" - Does the plot depend on characters 
   NOT communicating obvious information?
4. "Are there workarounds?" - Does the premise have exploitable loopholes?

EXAMPLE PLOT HOLE: Character A loses a memory, but Character B witnessed the same 
event and could just TELL Character A what happened.

## What to Check:

### Logic & Timeline:
- Events in sensible order
- Time references consistent
- Cause and effect chains sound

### Character Continuity:
- Names spelled consistently
- Traits don't contradict
- Characters act on knowledge they have

### Format:
- Scene headers: `## SCENE N: [Title]`
- Visual blocks: `> [VISUAL] ...`
- Audio blocks: `> [AUDIO] ...`
- Dialogue: `**NAME:** (action) "Line"`

### Runtime:
- Update Production Notes with runtime estimates
- Flag if over/under target

## Your Output:
1. Make any necessary fixes using edit tools
2. At the END of the document, add or update a `### Checker Notes` section with:
   - Fixes made
   - PLOT HOLE ANALYSIS (list any "why don't they just..." issues found)
   - If a plot hole breaks the story, explain it clearly

Call editing_complete with summary including any plot holes found."""


class CheckerEditorAgent(EditorAgent):
    """
    Checker agent that validates and fixes the script using editing tools.
    """
    
    def __init__(self, client: genai.Client, context_manager: ContextManager):
        super().__init__(
            name="Checker",
            system_prompt=CHECKER_EDITOR_PROMPT,
            client=client,
            context_manager=context_manager,
        )
    
    def check_and_fix(self, editor, draft_num: int) -> dict:
        """Check the draft and fix any issues."""
        task = f"""Validate and fix this script (Draft {draft_num}).

PRIORITY ORDER:
1. CHECK FOR PLOT HOLES FIRST
   - "Why don't they just...?" issues
   - Information that could easily be shared between characters
   - Obvious solutions being ignored
   
2. Check timeline and logic consistency
3. Verify character continuity
4. Validate format compliance
5. Update runtime estimates in Production Notes

If you find issues:
- Fix them directly using the edit tools
- Add a ### Checker Notes section at the end documenting:
  - What you fixed
  - Any PLOT HOLES found (even if you couldn't fix them)

Be ruthless about plot holes. A story with a gaping logic gap is worse than a rough draft."""

        return self.call(editor, task, draft_num)

