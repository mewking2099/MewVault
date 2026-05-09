# /teach $ARGUMENTS

Enter pedagogical mode for a learning track. Loads the registry-first, 5-step-cap, why-before-what rules. Persists for the rest of the session until `/wrap`.

`$ARGUMENTS` is the topic — e.g. `/teach rust`, `/teach godot`. If omitted, infer from the currently open project (inside `game-lab/` → godot; inside `wiki/learning/<topic>/` → that topic).

---

## Step 1 — Identify topic and locate registries

**Wiki learning path** (topic ≠ godot or no game project context):
- Learning path root: `wiki/learning/<topic>/`
- Registry: `wiki/learning/<topic>/concepts-learned.md`
- Session log: `wiki/learning/<topic>/Learning_Path.md`
- Sessions folder: `wiki/learning/<topic>/sessions/`
- Resources: `wiki/learning/<topic>/resources.md`

If the learning path doesn't exist, offer to create it:
> "No learning path found for '<topic>'. Create it with `mew new learning-path <topic>`?"

**Godot mode** (topic = `godot` or inside `game-lab/`):
- Project: current game project in `game-lab/<project>/`
- Concept registry: `game-lab/<project>/concepts-learned.md`
- Mechanics registry: `game-lab/<project>/mechanics-built.md`
- Session log: `game-lab/<project>/Project_Status.md` (update `last_session`)
- No separate Learning_Path.md — session notes go in `game-lab/<project>/sessions/` if the folder exists

---

## Step 2 — Registry scan

Read `concepts-learned.md` fully. Build two lists:
- **Known**: entries marked `[x]` — don't re-teach these unless asked
- **Orphans**: entries marked `[x]` but no `wiki:` path in the entry line

If orphans exist, surface them first:
```
⚠ Orphaned concepts (marked learned, no wiki note yet):
  - <concept> — explain again or write the note now?
```
Ask: "Handle orphans first, or skip?" This is non-blocking.

**Godot mode only:** also read `mechanics-built.md`. Note what's already been built. Never suggest rebuilding a shipped mechanic.

---

## Step 3 — Session kickoff

Count existing sessions: `len(sessions/*.md)` → next session number is N+1.

Announce:
```
/teach <topic> — Session N

Known: <count> concepts  |  Orphans: <count>
Cap: 5 new concepts this session.

What do you want to learn today?
```

If the user doesn't specify, propose the next logical concept from the `## Core` section of the registry (first unchecked `[ ]` entry).

---

## Step 4 — Teaching rules (active for the whole session)

Apply these rules to every response while in `/teach` mode:

**Rule 1 — Registry-first:**
Before explaining any concept, grep `concepts-learned.md`. If `[x]` and has a `wiki:` path → reference it, don't re-teach. If `[x]` but no `wiki:` path → it's an orphan, note that.

**Rule 2 — 5-step cap:**
No more than 5 *new* concepts introduced per session. Count each distinct concept as one step. Continuation steps on an already-introduced concept do not count. When the cap is reached:
> "That's 5 new concepts for today — solid session. Run `/wrap` to capture them, or keep going if you're in a flow."

**Rule 3 — Why before what:**
For every new concept: one paragraph of motivation (why it exists, what problem it solves) before any mechanics or syntax. For already-covered concepts: skip the why.

**Rule 4 — Mistakes are pedagogy:**
When the user makes an error, ask what they think happened before explaining. No silent fixes. Example:
> "What do you think went wrong there?"

**Rule 5 — End with /wrap:**
Remind the user at natural stopping points: "Run `/wrap` to log this session and write wiki notes."

---

## Step 5 — Godot-specific additions

When in Godot mode:

- Before suggesting any implementation: grep `mechanics-built.md` by keyword. If already built, reference the existing solution rather than re-implementing.
- After building something new: ask "Add this to mechanics-built.md?" and write the entry:
  `- <mechanic description> (session N) — <scene or script file>`
- Apply the same 5-step cap and why-before-what rules.
- Registry concepts are Godot-engine-specific (GDScript patterns, node types, signals) — not general programming concepts.

---

## Step 6 — Session tracking

Track internally (in conversation context, not written to disk):
- `session_number`: N (from step 3)
- `concepts_introduced`: [] (add to this as each new concept is taught)
- `concepts_checked`: [] (concepts the user confirms they understand)

This state is used by `/wrap` to run lesson-wrap. No files are written during the session itself — only on `/wrap`.

---

## Rules

- Never write to `concepts-learned.md`, wiki notes, or session files during the session. Write only on `/wrap`.
- Never rebuild a mechanic that exists in `mechanics-built.md` (Godot mode).
- The 5-step cap is advisory, not a hard stop — user can continue if they want to.
- If the user runs `/wrap` mid-session, run the lesson-wrap protocol immediately (see `/wrap` command).
- `wiki_note:` path format in registry: `concepts/<topic>/<kebab-case-concept>.md` (relative to wiki silo root).
