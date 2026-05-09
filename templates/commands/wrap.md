# /wrap

End the current session. Update timestamps, offer clean-up actions, return to vault overview.

---

## Step 1 — Identify active project

From conversation context, determine which project was active. If ambiguous, ask:
> "Which project should I wrap? (or 'none' to skip project update)"

---

## Step 2 — Update Project_Status.md

If a project was active:
1. Propose updates to `last_wrap` (set to today), `last_session` (set to today), `next_action` (confirm with user), and `phase_status` (if it changed).
2. Show the proposed diff and ask: "Update Project_Status.md with these changes?"
3. Write only on explicit approval.

---

## Step 3 — Lesson-wrap protocol (only if in `/teach` mode)

Triggered when this session involved `/teach` or learning-track work.

1. List every concept introduced or confirmed understood this session (from `concepts_introduced` and `concepts_checked` tracked during the session).
2. For each new concept (not already `[x]` in `concepts-learned.md`):
   - Draft an atomic wiki note at `wiki/concepts/<topic>/<kebab-case-concept>.md`:
     ```markdown
     ---
     title: <concept>
     created: YYYY-MM-DD
     updated: YYYY-MM-DD
     type: concept
     tags: [<topic>]
     status: draft
     promoted_from: wiki/learning/<topic>/concepts-learned.md
     ---

     # <concept>

     <one-paragraph explanation, cleaned up from session>
     ```
   - Show draft. Ask: "Write this note? (yes / skip / edit)"
3. **Transactional rule:** approved note → write the file AND update registry entry to `[x] <concept> (YYYY-MM-DD) — sessions/session-NN.md — wiki: concepts/<topic>/<kebab-case>.md`. Skipped → mark `[x]` but append no `wiki:` path. Never partial.
4. **Orphan check for Godot mode:** for each new mechanic built this session, ask: "Add to mechanics-built.md?" Write only on approval.
5. **Session log:** after all concepts are handled, write `wiki/learning/<topic>/sessions/session-NN.md`:
   ```markdown
   ---
   type: session-log
   topic: <topic>
   date: YYYY-MM-DD
   session: N
   ---

   # Session N — YYYY-MM-DD

   Concepts covered: <comma-separated list>
   New wiki notes: <list or "(none)">
   Next: <what to tackle next session>
   ```
   Then append a summary entry to `Learning_Path.md` under `## Sessions`:
   ```
   ### Session N — YYYY-MM-DD
   Concepts covered: <list>
   New [x] in registry: <list>
   Wiki notes created: <list>
   Next: <next focus>
   ```

---

## Step 4 — Phase transition check (UX projects only)

If the active project is a UX project and `phase_status` looks complete (user said "done", "finished phase", or artifacts are clearly complete):
1. Propose a phase summary (≤150 words).
2. Ask: "Advance to Phase <N+1>? (approve / edit / skip)"
3. On approval: increment `current_phase`, set `phase_status: in_progress`, write to `Project_Status.md`.
4. **If advancing to Phase 4:** add a note: "Phase 4 starts with Figma sync — say 'sync figma' when ready."

---

## Step 5 — Findings injection offer (UX Phase 3 → code project)

If the active UX project just completed Phase 3 (audit):
Ask: "Inject audit findings into a code project? (name it, or skip)"

If yes:
1. Read all `03_audit/*.md` files.
2. Identify findings with `severity: critical | major | minor`.
3. Ask which code project to inject into.
4. For each finding: create a stub issue in `software-projects/<target>/proposals/active/<finding-slug>/` with a pre-populated `status.yaml`.
5. Confirm before writing.

---

## Step 6 — Commit suggestion

Check for uncommitted changes by running: `mew sync` (or note "there may be uncommitted changes").
If likely: suggest a commit message. **Do not auto-commit.**

Example:
> Suggested commit: `"wrap: acme-rebrand phase 2 synthesis complete"`
> Run `git commit -m "..."` when ready.

---

## Step 7 — Vault overview

Display the vault overview (same format as `/start` Step 1) so the next drill-in is easy.

---

## Rules

- Never auto-commit. Suggest only.
- Never update `Project_Status.md` without explicit user approval.
- Lesson-wrap is transactional — write note and registry entry together, or neither.
- Phase transition requires explicit approval of the proposed summary.
- If no project was active this session, skip Steps 2–5 and go straight to vault overview.
