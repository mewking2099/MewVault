---
name: plan-orchestrate
description: Read a MewKing plan document, decompose it into tasks, assign the right subagent and model to each, and emit ready-to-paste Agent() call prompts. Use when the user says "orchestrate this plan", "give me agent prompts for each step", or has a plan.md they want to drive through subagents.
origin: ECC (adapted for mewvault)
---

# Plan Orchestrate

Bridge a plan document to per-step Agent() calls. Generative only — never executes the agents itself. The user pastes each call when ready.

## When to Activate

- User has a plan document (proposals/active/<feature>/plan.md) and wants to drive it through subagents
- User says "orchestrate this plan", "give me agent prompts for each step"
- A MewKing plan is approved and the user wants to execute it task-by-task

**Skip when:** The plan is a single task (just execute it directly) or is empty/unreadable.

## MewVault Agent Catalogue

Pick from these agents. Match the agent to the task type:

| Agent | Use for |
|-------|---------|
| `mew-planner` | Architecture decisions, approach proposals, risk decomposition |
| `mew-coder` | Code implementation, refactoring, test generation |
| `mew-designer` | UX decisions, Figma review, component specs |
| `mew-gamedev` | GDScript, game mechanics, Godot patterns |
| `mew-learner` | Research, concept distillation, wiki updates |
| `mew-archivist` | Log entries, session wrap, Project_Status updates |
| `code-reviewer` (skill) | Code quality review — call via subagent-driven-development |

## Model Routing (from subagent-model-routing.md)

| Task | Model |
|------|-------|
| Search / explore | Haiku |
| Single-file mechanical change | Haiku |
| Multi-file implementation | Sonnet |
| Architecture / design | Opus |
| Security review | Opus |

## Process

### Step 1: Read the plan

```
Read proposals/active/<feature>/plan.md (or user-specified path)
```

Extract:
- Goal (one sentence)
- Architecture notes
- File map
- Tasks (numbered list)

### Step 2: Decompose into steps

For each task in the plan:
1. Identify the task type (implement / review / research / document)
2. Assign the best agent from the catalogue
3. Select the appropriate model
4. Identify what context the agent needs (files, prior task output, constraints)

### Step 3: Emit Agent() prompts

For each step, emit a ready-to-paste Agent() call:

```python
# Step N: [Task name]
Agent({
  "description": "[3-5 word description]",
  "subagent_type": "[agent-name]",
  "model": "[haiku|sonnet|opus]",
  "prompt": """
[Task context — include:]
- What to do (specific, not vague)
- Which files to read/modify (exact paths)
- What constraints apply (don't touch X, follow Y pattern)
- What to return in the summary

[Paste relevant plan section here]
"""
})
```

**Never** include your full session history in the agent prompt. Construct exactly what the agent needs.

### Step 4: Sequencing note

Identify dependencies between steps:
- **Independent steps:** can be dispatched in parallel (emit all Agent() calls in one message)
- **Dependent steps:** must run in sequence (note "wait for Step N output before running Step M")

## Example Output

```
Plan: DSaaS Phase 3 — Supabase Auth

Step 1 (independent) — Schema design
Agent({
  description: "Design auth schema",
  subagent_type: "mew-planner",
  model: "opus",
  prompt: "Design the Supabase auth schema for DSaaS..."
})

Step 2 (independent) — Explore existing auth code
Agent({
  description: "Map existing auth code",
  subagent_type: "mew-coder",
  model: "haiku",
  prompt: "Read src/auth/** and list all files that handle authentication..."
})

Step 3 (after Steps 1+2) — Implement
Agent({
  description: "Implement Supabase auth",
  subagent_type: "mew-coder",
  model: "sonnet",
  prompt: "Implement the auth schema from Step 1 output. Context files: [Step 2 output]..."
})
```

## Rules

- Emit prompts as plain text the user can copy — not as executable code
- Always note which steps can run in parallel
- Never guess file paths — say "read the plan's file map section for exact paths"
- If the plan is MewKing tier, verify `plan_approved: true` before emitting prompts
