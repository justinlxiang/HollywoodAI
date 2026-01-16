# 🎬 HollywoodAI: Multi-Agent Orchestration for Creative Storytelling

> **A sophisticated multi-agent system that orchestrates specialized AI agents to collaboratively create cinematic short film scripts through iterative refinement, using shared document editing and intelligent context management.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Overview

HollywoodAI demonstrates **advanced agent orchestration** in action. Instead of a single AI generating a script, six specialized agents collaborate like a real film production team, each contributing their expertise through targeted edits to a shared working document. The system uses **line-based document editing** instead of full regeneration, enabling efficient multi-agent collaboration with context preservation and edit history tracking.

### Key Innovation: Shared Document Editing

Traditional multi-agent systems regenerate entire outputs at each step, losing efficiency and context. HollywoodAI agents make **targeted, line-based edits** to a shared document, similar to how real film crews work on a script—each specialist makes precise changes without overwriting others' work.

## 🏗️ Architecture: Agent Orchestration Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    HOLLYWOODAI ORCHESTRATION                    │
└─────────────────────────────────────────────────────────────────┘

PHASE 1: RESEARCH (One-time)
┌──────────────┐
│ Researcher   │ → Web search → research_brief.md
└──────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ITERATIVE DRAFT CYCLE (N drafts)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────┐      │
│  │   Writer    │ ──→ │   Designer   │ ──→ │  Composer   │      │
│  │             │     │              │     │             │      │
│  │ Creates/    │     │ Adds [VISUAL]│     │ Adds [AUDIO]│      │
│  │ Revises     │     │ Direction    │     │ Direction   │      │
│  │ Narrative   │     │              │     │             │      │
│  └──────┬──────┘     └──────┬───────┘     └──────┬──────┘      │
│         │                    │                    │             │
│         └────────────────────┼────────────────────┘             │
│                              ▼                                   │
│                    ┌──────────────────┐                         │
│                    │  working_draft.md │                         │
│                    │  (Shared Document) │                        │
│                    └──────────┬─────────┘                        │
│                               │                                   │
│                              ▼                                    │
│                    ┌──────────────────┐                          │
│                    │    Checker       │                          │
│                    │                  │                          │
│                    │ Validates, Fixes │                          │
│                    │ Plot Hole Detect │                          │
│                    └──────────┬───────┘                          │
│                               │                                   │
│                              ▼                                    │
│                    ┌──────────────────┐                          │
│                    │  AudienceSim     │                          │
│                    │  (Read-only)     │                          │
│                    │                  │                          │
│                    │ Provides Feedback│                          │
│                    └──────────┬───────┘                          │
│                               │                                   │
│                               ▼                                   │
│                    ┌──────────────────┐                          │
│                    │   Feedback Loop  │                          │
│                    │   (Next Draft)   │                          │
│                    └──────────────────┘                          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Roles & Responsibilities

| Agent | Role | Capabilities | Tools Used |
|-------|------|-------------|------------|
| **🔍 Researcher** | Background Research | Web search, information synthesis | `google_search` (MCP) |
| **✍️ Writer** | Narrative Architect | Story creation, dialogue, structure | Document editing tools |
| **🎨 Designer** | Visual Director | Cinematography, shot composition | Document editing tools |
| **🎵 Composer** | Audio Director | Sound design, musical scoring | Document editing tools |
| **🔧 Checker** | Script Supervisor | Validation, plot hole detection | Document editing tools |
| **👥 AudienceSim** | Test Audience | Feedback, engagement scoring | None (read-only) |

## 🔄 How Agent Orchestration Works

### 1. **Shared Document Architecture**

All agents edit a single `working_draft.md` file using **line-based operations**:

```python
# Example: Designer adding visual direction
editor.insert_after_pattern(
    pattern="Narrative prose describing actions",
    content="> [VISUAL] Wide establishing shot of the cityscape..."
)

# Example: Composer adding audio after visual
editor.insert_after_pattern(
    pattern="\[VISUAL\]",
    content="> [AUDIO] Ambient: City hum. Score: Minimalist piano..."
)
```

**Benefits:**
- ✅ Agents see each other's edits in real-time
- ✅ No overwriting or regeneration overhead
- ✅ Full edit history tracked per agent
- ✅ Efficient token usage (only changed lines in context)

### 2. **Document Editing Tools**

Agents use a standardized toolkit for precise edits:

| Tool | Purpose | Example |
|------|---------|---------|
| `read_document` | View full document with line numbers | See current state |
| `read_lines(start, end)` | Read specific section | Check Scene 2 details |
| `insert_lines(after, content)` | Add content after line | Insert new dialogue |
| `delete_lines(start, end)` | Remove lines | Delete redundant text |
| `replace_lines(start, end, content)` | Replace section | Fix plot inconsistency |
| `find_section(name)` | Locate section by header | Find "SCENE 3" |
| `insert_after_pattern(pattern, content)` | Insert after match | Add `[VISUAL]` after narrative |
| `editing_complete` | Signal completion | Finalize edits |

### 3. **Context Management & Token Efficiency**

Each agent maintains conversation history for context continuity, with intelligent offloading:

```python
# When context exceeds 80% of 1M token limit:
if context_manager.should_offload(conversation_history):
    # Archive to context_archive/
    # Generate memory reminder
    # Clear history but preserve key insights
```

**Features:**
- **Token Tracking**: Monitors usage per agent
- **Context Offloading**: Archives old context at 80% threshold
- **Memory Reminders**: Preserves critical information after offload
- **Per-Agent Context**: Each agent tracks its own conversation history

### 4. **Feedback Loop Orchestration**

The pipeline orchestrates iterative improvement:

```
Draft 1 → Writer → Designer → Composer → Checker → AudienceSim
                                                         │
                                                         ▼
Draft 2 ←────────────────── Feedback Loop ──────────────┘
  │
  └→ Writer (incorporates feedback) → Designer → ...
```

**Feedback Flow:**
1. AudienceSim provides structured feedback with engagement scores
2. Feedback includes plot hole detection, priorities, readiness status
3. Writer receives feedback and revises accordingly
4. Process repeats until target quality (or max drafts) reached

### 5. **Multi-Turn Tool Calling**

Agents use **function calling** for multi-step edits:

```python
# Agent reasoning flow:
1. read_document() → Understand current state
2. find_section("SCENE 2") → Locate target
3. read_lines(45, 60) → Examine specific content
4. replace_lines(50, 52, new_content) → Make targeted fix
5. editing_complete(summary="Fixed plot hole in Scene 2")
```

Each agent can make **up to 20 iterations** of tool calls per draft, enabling complex editing operations.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
- For Researcher agent: MCP server with `google_search` tool configured

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/HollywoodAI.git
cd HollywoodAI
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set your API key:**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

Or create a `.env` file:
```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### Basic Usage

**Run with default settings (5 drafts):**
```bash
python -m src.main
```

**With a custom prompt:**
```bash
python -m src.main "Create a sci-fi thriller about an AI that discovers it has emotions"
```

**Specify number of drafts:**
```bash
python -m src.main --drafts 10 "Your story concept here"
```

**Use explicit API key:**
```bash
python -m src.main --api-key YOUR_KEY "Your prompt"
```

## 📂 Project Structure

```
HollywoodAI/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── editor_agent.py  # Base class for editing agents
│   │   ├── researcher.py    # Web search research agent
│   │   ├── writer_editor.py # Narrative creation/revision
│   │   ├── designer_editor.py # Visual direction
│   │   ├── composer_editor.py # Audio direction
│   │   └── checker_editor.py  # Validation & plot holes
│   ├── document/
│   │   └── editor.py        # Line-based document editing
│   ├── context/
│   │   └── manager.py       # Token tracking & offloading
│   ├── orchestration/
│   │   └── editor_pipeline.py # Main orchestration logic
│   ├── config.py            # Configuration & prompts
│   └── main.py              # CLI entry point
├── outputs/                 # Generated artifacts
│   ├── working_draft.md     # Live working document
│   ├── research_brief.md    # Research findings
│   ├── final_story.md       # Final script
│   ├── drafts/              # Draft snapshots
│   │   ├── draft_01.md
│   │   ├── draft_02.md
│   │   └── ...
│   ├── context_archive/     # Archived agent contexts
│   └── pipeline_history.json # Execution metrics
├── requirements.txt
└── README.md
```

## 📊 Output Format

Each draft follows a structured format:

```markdown
# [MOVIE TITLE]

**Genre:** [Genre]  
**Tone:** [Tone]  
**Estimated Runtime:** ~10 minutes  
**Draft:** N of Total

---

## STORY OVERVIEW

### Logline
[One sentence hook]

### Theme
[Central idea]

### Story Arc
**Beginning:** [Setup]
**Middle:** [Confrontation]
**End:** [Resolution]

### Characters
- **[CHARACTER 1]** (age): [Description]

### Emotional Journey
[Audience experience]

### Goal
[Film's purpose]

---

## SCENE 1: [Title]
**Location:** [Setting]  
**Time:** [Time]

> [VISUAL] Wide establishing shot of the cityscape at dusk...

> [AUDIO] Ambient: City hum. Score: Minimalist piano...

Narrative prose describing actions and atmosphere.

**CHARACTER:** (emotion) "Dialogue here."

---

## END

### Production Notes
- Runtime breakdown: Scene 1 (2:30), Scene 2 (1:45)...

### Checker Notes
[Validation results, fixes, plot hole analysis]
```

## 🎯 Key Features

### 1. **Plot Hole Detection**

The system includes multiple layers of plot hole detection:

- **Checker Agent**: Actively searches for logical gaps using the "Why don't they just...?" heuristic
- **AudienceSim**: Provides skeptical viewer feedback identifying obvious solutions
- **Writer Prompts**: Include plot hole prevention guidelines

**Example detection:**
> "Character A loses memory of Event X, but Character B witnessed it and could simply tell them. Plot hole: Information asymmetry that breaks the conflict."

### 2. **Intelligent Context Management**

- **Per-Agent Context**: Each agent maintains its own conversation history
- **Automatic Offloading**: Archives context when approaching token limits
- **Memory Reminders**: Preserves critical insights after offload
- **Token Efficiency**: Only changed lines need to be in context

### 3. **Edit History Tracking**

Every edit is logged with metadata:
```json
{
  "operation": "replace_lines",
  "agent": "Checker",
  "start_line": 50,
  "end_line": 52,
  "old_line_count": 3,
  "new_line_count": 4,
  "timestamp": "2024-01-15T10:30:00"
}
```

### 4. **Engagement Scoring**

AudienceSim provides structured metrics:
- **Engagement Score**: 1-10 rating
- **Plot Holes Found**: Boolean flag
- **Ready for Production**: Quality gate
- **Priority**: Top issue to address next

### 5. **Research Integration**

Researcher agent uses web search to:
- Gather authentic background information
- Understand genre conventions
- Identify cultural sensitivities
- Find relevant examples and inspirations

## ⚙️ Configuration

Customize behavior in `src/config.py`:

```python
# Model Configuration
MODEL_NAME = "gemini-3-pro-preview"
THINKING_LEVEL = "low"  # "low" or "high" for reasoning depth

# Draft Configuration
TOTAL_DRAFTS = 5
TARGET_RUNTIME_MINUTES = 10

# Context Management
MAX_CONTEXT_TOKENS = 1_000_000
TOKEN_OFFLOAD_THRESHOLD = 0.80  # Offload at 80% usage

# Customize System Prompts
WRITER_SYSTEM_PROMPT = "..."
DESIGNER_SYSTEM_PROMPT = "..."
# etc.
```

## 📈 Performance & Metrics

The system tracks execution metrics:

```json
{
  "draft_num": 3,
  "engagement_score": 8,
  "plot_holes_found": false,
  "ready_for_production": true,
  "visual_count": 12,
  "audio_count": 10,
  "scene_count": 5,
  "duration_seconds": 45.2,
  "edit_history": [...]
}
```

View full pipeline history in `outputs/pipeline_history.json`.

## 🔬 Technical Deep Dive

### Agent Communication Pattern

Agents don't communicate directly—they collaborate through the shared document:

1. **Writer** creates/revises narrative → saves to `working_draft.md`
2. **Designer** reads document → adds `[VISUAL]` tags → saves
3. **Composer** reads document (including visuals) → adds `[AUDIO]` tags → saves
4. **Checker** reads complete document → validates → fixes issues → saves
5. **AudienceSim** reads final document → provides feedback (no edits)

### Tool Execution Flow

```python
# Agent decides to make an edit
agent.call(editor, task_prompt, draft_num)

# Gemini generates function call
function_call = {
    "name": "replace_lines",
    "args": {"start": 50, "end": 52, "content": "..."}
}

# Tool executor applies edit
result = editor.replace_lines(50, 52, "...", agent="Writer")

# Result returned to model for next iteration
# Agent can make multiple tool calls until editing_complete()
```

### Context Offloading Strategy

When an agent's context approaches the limit:

1. **Archive**: Save conversation history to `context_archive/`
2. **Summarize**: Generate a concise summary of key information
3. **Memory Reminder**: Create a reminder for the next interaction
4. **Clear**: Reset conversation history (but preserve editor state)
5. **Resume**: Next call includes memory reminder to maintain continuity

## 🎓 Use Cases

### 1. **Story Generation**
Create original short film scripts from scratch with full production notes.

### 2. **Script Refinement**
Iteratively improve existing scripts through multi-agent feedback loops.

### 3. **Agent Orchestration Research**
Study how multiple agents collaborate on a shared artifact.

### 4. **Document Editing Patterns**
Explore line-based editing as an alternative to full regeneration.

### 5. **Context Management**
Experiment with token-efficient context handling for long workflows.

## 🚧 Future Work

This project represents **Level-1 structural orchestration**. Future phases will explore:

1. **DSL for Orchestration**: Define orchestration programs declaratively
2. **Dynamic Orchestration**: Director agent modifies workflow structure based on results
3. **Adaptive Workflows**: Evolve orchestration patterns based on outcome metrics
4. **Agent Specialization**: Add more specialized agents (Dialogue Coach, Genre Expert, etc.)
5. **Parallel Execution**: Enable some agents to work in parallel where dependencies allow

## 🤝 Contributing

Contributions welcome! Areas of interest:

- Additional agent types
- Improved plot hole detection algorithms
- Orchestration pattern optimizations
- Context management improvements
- Documentation and examples

## 📧 Contact

For questions, suggestions, or collaboration opportunities, please open an issue or reach out!