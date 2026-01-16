"""
Editor Pipeline - Uses document editing tools instead of full regeneration.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Optional
from google import genai
from google.genai import types

from ..config import (
    GEMINI_API_KEY,
    TOTAL_DRAFTS,
    DRAFTS_DIR,
    FINAL_STORY_PATH,
    OUTPUT_DIR,
    MODEL_NAME,
    THINKING_LEVEL,
    AUDIENCE_SIM_SYSTEM_PROMPT,
)
from ..context.manager import ContextManager
from ..document.editor import DocumentEditor
from ..agents.researcher import ResearcherAgent
from ..agents.writer_editor import WriterEditorAgent
from ..agents.designer_editor import DesignerEditorAgent
from ..agents.composer_editor import ComposerEditorAgent
from ..agents.checker_editor import CheckerEditorAgent


class EditorPipeline:
    """
    Pipeline that uses document editing tools.
    
    Agents edit a shared working document using line-based operations
    instead of regenerating the full content each time.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the pipeline.
        
        Args:
            api_key: Optional Gemini API key
        """
        api_key = api_key or GEMINI_API_KEY
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it in your environment or .env file."
            )
        
        self.client = genai.Client(api_key=api_key)
        self.context_manager = ContextManager(self.client)
        
        # Initialize agents
        self.researcher = ResearcherAgent(self.client, self.context_manager)
        self.writer = WriterEditorAgent(self.client, self.context_manager)
        self.designer = DesignerEditorAgent(self.client, self.context_manager)
        self.composer = ComposerEditorAgent(self.client, self.context_manager)
        self.checker = CheckerEditorAgent(self.client, self.context_manager)
        
        # Working document path
        self.working_doc_path = os.path.join(OUTPUT_DIR, "working_draft.md")
        
        # Ensure directories exist
        os.makedirs(DRAFTS_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # History
        self.history: list[dict] = []
        self.research: str = ""
    
    def _get_audience_feedback(self, content: str, draft_num: int, previous_feedback: str) -> dict:
        """
        Get audience feedback (read-only, no editing).
        
        Args:
            content: Current draft content
            draft_num: Current draft number
            previous_feedback: Previous feedback for comparison
            
        Returns:
            Dict with feedback
        """
        prompt = f"""## AUDIENCE FEEDBACK REQUEST - Draft {draft_num}

Watch this short film as an audience member and provide feedback.

### Script to Review:

{content}

{"### Your Previous Feedback (Draft " + str(draft_num - 1) + "):" + chr(10) + previous_feedback + chr(10) + "Consider whether your previous concerns have been addressed." if previous_feedback else ""}

Provide structured feedback. Use XML tags for key metrics that need to be extracted:

# Audience Feedback - Draft {draft_num}

## Overall Impression
[2-3 sentences on gut reaction]

## Plot Hole Check (REQUIRED)
Ask yourself: "Why don't they just...?"
- [List ANY logical gaps]
- [If a character forgets something, can another character tell them?]
- [Write "None found" ONLY if genuinely no issues]

<plot_holes_found>true or false</plot_holes_found>

## What's Working
- [Strength 1]
- [Strength 2]
- [Strength 3]

## Areas for Improvement
- [Issue 1]: [Suggestion]
- [Issue 2]: [Suggestion]

## Priority for Next Draft
<priority>[Single most important thing to address]</priority>

<engagement_score>[1-10, integer only. Major plot hole = max score 6]</engagement_score>

<ready_for_production>true or false</ready_for_production>"""

        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=AUDIENCE_SIM_SYSTEM_PROMPT,
                thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
            ),
        )
        
        feedback = response.text
        
        # Extract structured data from XML tags
        import re
        
        def extract_xml_tag(text: str, tag: str) -> str | None:
            """Extract content from an XML tag."""
            match = re.search(rf"<{tag}>\s*(.*?)\s*</{tag}>", text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else None
        
        def extract_bool(text: str, tag: str) -> bool | None:
            """Extract boolean from XML tag."""
            value = extract_xml_tag(text, tag)
            if value is None:
                return None
            return value.lower() in ("true", "yes", "1")
        
        def extract_int(text: str, tag: str) -> int | None:
            """Extract integer from XML tag."""
            value = extract_xml_tag(text, tag)
            if value is None:
                return None
            # Handle cases like "7/10" or "7 out of 10"
            match = re.search(r"(\d+)", value)
            return int(match.group(1)) if match else None
        
        engagement_score = extract_int(feedback, "engagement_score")
        plot_holes_found = extract_bool(feedback, "plot_holes_found")
        ready_for_production = extract_bool(feedback, "ready_for_production")
        priority = extract_xml_tag(feedback, "priority")
        
        return {
            "feedback": feedback,
            "engagement_score": engagement_score,
            "plot_holes_found": plot_holes_found,
            "ready_for_production": ready_for_production,
            "priority": priority,
        }
    
    def run_research(self, user_message: str) -> str:
        """Run the research phase."""
        if not user_message:
            return ""
        
        print("\n" + "="*60)
        print("RESEARCH PHASE")
        print("="*60)
        
        print(f"\nINPUT:\nUser Message: {user_message}")
        result = self.researcher.call({
            "message": user_message,
            "draft_num": 0,
        })
        
        print(f"\nOUTPUT:\n{result}")
        print("-" * 60)
        
        self.research = result.get("research", "")
        
        if self.research:
            research_path = os.path.join(OUTPUT_DIR, "research_brief.md")
            with open(research_path, 'w', encoding='utf-8') as f:
                f.write(self.research)
            print(f"  Research saved: {research_path}")
        
        return self.research
    
    def run_draft(
        self,
        editor: DocumentEditor,
        draft_num: int,
        total_drafts: int,
        previous_feedback: str = "",
        user_message: str = "",
        research: str = "",
    ) -> dict:
        """
        Run a single draft through all editing agents.
        
        Args:
            editor: Shared document editor
            draft_num: Current draft number
            total_drafts: Total number of drafts
            previous_feedback: Feedback from previous draft
            user_message: Initial user prompt (first draft only)
            research: Research brief (first draft only)
            
        Returns:
            Dict with results
        """
        print(f"\n{'='*60}")
        print(f"DRAFT {draft_num} of {total_drafts}")
        print(f"{'='*60}")
        
        start_time = datetime.now()
        
        # Step 1: Writer
        print(f"\n[1/5] Writer - {'Creating' if draft_num == 1 else 'Revising'} narrative...")
        print("-" * 60)
        if draft_num == 1:
            writer_input = f"User Message: {user_message}\nResearch: {research[:200] if research else 'None'}..."
            print(f"INPUT:\n{writer_input}")
            writer_result = self.writer.create_initial_draft(
                editor, user_message, research, draft_num, total_drafts
            )
        else:
            writer_input = f"Feedback: {previous_feedback[:300]}..."
            print(f"INPUT:\n{writer_input}")
            writer_result = self.writer.revise_draft(
                editor, previous_feedback, draft_num, total_drafts
            )
        print(f"\nOUTPUT:\n{writer_result}")
        print("-" * 60)
        
        # Step 2: Designer
        print("\n[2/5] Designer - Adding visual direction...")
        print("-" * 60)
        designer_input = f"Task: Add [VISUAL] direction tags throughout Draft {draft_num}"
        print(f"INPUT:\n{designer_input}")
        designer_result = self.designer.add_visuals(editor, draft_num)
        print(f"\nOUTPUT:\n{designer_result}")
        print("-" * 60)
        
        # Step 3: Composer  
        print("\n[3/5] Composer - Adding audio direction...")
        print("-" * 60)
        composer_input = f"Task: Add [AUDIO] direction tags throughout Draft {draft_num}"
        print(f"INPUT:\n{composer_input}")
        composer_result = self.composer.add_audio(editor, draft_num)
        print(f"\nOUTPUT:\n{composer_result}")
        print("-" * 60)
        
        # Step 4: Checker
        print("\n[4/5] Checker - Validating and fixing...")
        print("-" * 60)
        checker_input = f"Task: Validate and fix Draft {draft_num} (check for plot holes, consistency, format)"
        print(f"INPUT:\n{checker_input}")
        checker_result = self.checker.check_and_fix(editor, draft_num)
        print(f"\nOUTPUT:\n{checker_result}")
        print("-" * 60)
        
        # Save this draft version
        draft_path = os.path.join(DRAFTS_DIR, f"draft_{draft_num:02d}.md")
        shutil.copy(editor.filepath, draft_path)
        print(f"  Draft saved: {draft_path}")
        
        # Step 5: Audience feedback
        print("\n[5/5] AudienceSim - Generating feedback...")
        print("-" * 60)
        content = editor.get_content()
        audience_input = f"Content length: {len(content)} chars, Draft {draft_num}"
        print(f"INPUT:\n{audience_input}")
        audience_result = self._get_audience_feedback(
            content, draft_num, previous_feedback
        )
        feedback = audience_result["feedback"]
        print(f"\nOUTPUT:\nFeedback: {feedback[:500]}...")
        print(f"  <engagement_score>: {audience_result.get('engagement_score', 'N/A')}")
        print(f"  <plot_holes_found>: {audience_result.get('plot_holes_found', 'N/A')}")
        print(f"  <ready_for_production>: {audience_result.get('ready_for_production', 'N/A')}")
        print(f"  <priority>: {audience_result.get('priority', 'N/A')}")
        print("-" * 60)
        
        # Append feedback as HTML comment
        with open(draft_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n---\n\n<!-- AUDIENCE FEEDBACK\n{feedback}\n-->")
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Count elements
        visual_count = content.count("[VISUAL]")
        audio_count = content.count("[AUDIO]")
        scene_count = content.count("## SCENE")
        
        result = {
            "draft_num": draft_num,
            "feedback": feedback,
            "engagement_score": audience_result.get("engagement_score"),
            "plot_holes_found": audience_result.get("plot_holes_found"),
            "ready_for_production": audience_result.get("ready_for_production"),
            "priority": audience_result.get("priority"),
            "visual_count": visual_count,
            "audio_count": audio_count,
            "scene_count": scene_count,
            "duration_seconds": duration,
            "edit_history": editor.get_edit_history(),
        }
        
        self.history.append(result)
        
        print(f"\n{'='*60}")
        print(f"Draft {draft_num} Complete! ({duration:.1f}s)")
        print(f"Scenes: {scene_count}, Visuals: {visual_count}, Audio: {audio_count}")
        if audience_result.get("engagement_score"):
            score = audience_result['engagement_score']
            status = "🚨 Plot holes!" if audience_result.get("plot_holes_found") else ""
            ready = "✅ Ready!" if audience_result.get("ready_for_production") else ""
            print(f"Engagement Score: {score}/10 {status} {ready}")
        print(f"{'='*60}")
        
        return result
    
    def run_all_drafts(self, user_message: str = "") -> str:
        """
        Run all drafts.
        
        Args:
            user_message: Initial prompt
            
        Returns:
            Path to final story
        """
        print("\n" + "="*60)
        print("STARTING MULTI-DRAFT MOVIE CREATION (Editor Mode)")
        print(f"Total Drafts: {TOTAL_DRAFTS}")
        print("="*60)
        
        # Research phase
        research = self.run_research(user_message)
        
        # Initialize working document
        editor = DocumentEditor(self.working_doc_path)
        editor.clear()  # Start fresh
        
        previous_feedback = ""
        
        for draft_num in range(1, TOTAL_DRAFTS + 1):
            result = self.run_draft(
                editor=editor,
                draft_num=draft_num,
                total_drafts=TOTAL_DRAFTS,
                previous_feedback=previous_feedback,
                user_message=user_message if draft_num == 1 else "",
                research=research if draft_num == 1 else "",
            )
            
            previous_feedback = result["feedback"]
        
        # Copy final to final_story.md
        shutil.copy(self.working_doc_path, FINAL_STORY_PATH)
        
        print(f"\n{'='*60}")
        print("ALL DRAFTS COMPLETE!")
        print(f"Final story: {FINAL_STORY_PATH}")
        print(f"{'='*60}")
        
        # Save history
        self._save_history()
        
        return FINAL_STORY_PATH
    
    def _save_history(self) -> str:
        """Save pipeline history."""
        filepath = os.path.join(OUTPUT_DIR, "pipeline_history.json")
        
        serializable = []
        for entry in self.history:
            serializable.append({
                "draft_num": entry["draft_num"],
                "engagement_score": entry.get("engagement_score"),
                "plot_holes_found": entry.get("plot_holes_found"),
                "ready_for_production": entry.get("ready_for_production"),
                "priority": entry.get("priority"),
                "visual_count": entry.get("visual_count", 0),
                "audio_count": entry.get("audio_count", 0),
                "scene_count": entry.get("scene_count", 0),
                "duration_seconds": entry.get("duration_seconds", 0),
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2)
        
        return filepath

