"""
Main entry point for the Multi-Agent Orchestration system.

Usage:
    python -m src.main
    python -m src.main "Create a sci-fi thriller about AI"
    python -m src.main --drafts 5
"""

import argparse
import os
import sys
from datetime import datetime

from .config import TOTAL_DRAFTS, FINAL_STORY_PATH, OUTPUT_DIR
from .orchestration import EditorPipeline


def print_banner():
    """Print the application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🎬 MULTI-AGENT ORCHESTRATION                                ║
║        Multi-Agent Movie Creation System                         ║
║                                                                  ║
║     Agents: Writer → Designer → Composer → Checker → Audience    ║
║     Model: Gemini 3 Pro                                          ║
║     Mode: Editor (line-based document editing)                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_summary(pipeline: EditorPipeline, final_path: str, total_time: float):
    """Print a summary of the run."""
    print("\n" + "="*60)
    print("RUN SUMMARY")
    print("="*60)
    
    print(f"\nTotal Drafts: {len(pipeline.history)}")
    print(f"Total Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    if pipeline.history:
        print(f"Average Time per Draft: {total_time/len(pipeline.history):.1f} seconds")
    
    # Engagement score progression
    scores = [h.get("engagement_score") for h in pipeline.history if h.get("engagement_score")]
    if scores:
        print(f"\nEngagement Score Progression: {' → '.join(str(s) for s in scores)}")
        print(f"Starting Score: {scores[0]}/10")
        print(f"Final Score: {scores[-1]}/10")
        if len(scores) > 1:
            improvement = scores[-1] - scores[0]
            print(f"Improvement: {'+' if improvement >= 0 else ''}{improvement} points")
    
    # Final draft stats
    if pipeline.history:
        final = pipeline.history[-1]
        print(f"\nFinal Draft Stats:")
        print(f"  Scenes: {final.get('scene_count', 'N/A')}")
        print(f"  Visual Directions: {final.get('visual_count', 'N/A')}")
        print(f"  Audio Directions: {final.get('audio_count', 'N/A')}")
    
    print(f"\nFinal Story: {final_path}")
    print(f"All Drafts: {os.path.join(OUTPUT_DIR, 'drafts/')}")
    print(f"Pipeline History: {os.path.join(OUTPUT_DIR, 'pipeline_history.json')}")
    print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Movie Creation System using Gemini 3 Pro"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="",
        help="Optional initial prompt/instructions for the story"
    )
    parser.add_argument(
        "--drafts",
        type=int,
        default=TOTAL_DRAFTS,
        help=f"Number of drafts to run (default: {TOTAL_DRAFTS})"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Gemini API key (defaults to GEMINI_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Validate API key
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: No API key provided.")
        print("Set GEMINI_API_KEY environment variable or use --api-key flag.")
        sys.exit(1)
    
    # Update draft count if specified
    if args.drafts != TOTAL_DRAFTS:
        print(f"Note: Running {args.drafts} drafts (default is {TOTAL_DRAFTS})")
        import src.config as config
        config.TOTAL_DRAFTS = args.drafts
    
    # Initialize pipeline
    print("Initializing pipeline...")
    try:
        pipeline = EditorPipeline(api_key=api_key)
    except Exception as e:
        print(f"ERROR: Failed to initialize pipeline: {e}")
        sys.exit(1)
    
    # Run the pipeline
    start_time = datetime.now()
    
    try:
        final_path = pipeline.run_all_drafts(user_message=args.prompt)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        print(f"Completed {len(pipeline.history)} drafts before interruption.")
        if pipeline.history:
            pipeline._save_history()
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        if pipeline.history:
            pipeline._save_history()
        sys.exit(1)
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    # Print summary
    print_summary(pipeline, final_path, total_time)
    
    print("\n✅ Movie creation complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
