---
name: godot-session-start
triggers: [start game session, continue game, pick up from last session, what's next in the game, resume game dev]
description: Session-start ritual for Godot projects — reads project state and proposes the next mechanic to build.
inject: always
---

# Skill: Godot Session Start

Run this ritual at the start of every game development session **before writing any code**.

## Step 1 — Read Project State

Read these files in order:
1. `game-lab/<project>/Project_Status.md` — current phase, mechanic backlog, what's done
2. `game-lab/<project>/wiki/scene-map.md` — current node tree and script attachments
3. `game-lab/<project>/wiki/game-design.md` — GDD, mechanic priority list
4. `game-lab/<project>/log.md` — last session summary

## Step 2 — Report Current State

Output a short status block:

```
## Session Start — <project>

**Last completed:** <mechanic or task from log>
**Scene state:** <summary of scene-map — key nodes present>
**Mechanic backlog (in order):**
  ✓ <done>
  → <NEXT — this session's target>
  · <pending>
  · <pending>
```

## Step 3 — Propose the Session Scope

State exactly what will be built this session — **one mechanic only**. Be specific:

> "This session: implement gravity + jump for the Player node. I'll add to `Player.gd`: `_physics_process` with gravity constant, jump impulse on `ui_accept`, `is_on_floor()` guard. Expected result: player falls and can jump."

Then ask: **"Confirm and I'll write it, or adjust the scope."**

Wait for confirmation before writing any code.

## Step 4 — After Confirmation

Write the smallest complete unit that can be tested in one Godot run:
- Single script or minimal addition to an existing script
- Include `print()` statements at key points so errors are easy to locate
- Never exceed what can be tested in a single run
- After the user tests, handle the error loop (see `godot-debug` skill)

## Session End

When the mechanic works:
1. Update `wiki/scene-map.md` with any new nodes or signal connections added
2. Create or update `wiki/mechanic-<name>.md`
3. Increment `mechanics_count` in `Project_Status.md`
4. Write a log entry in `log.md`
5. Suggest a commit message
