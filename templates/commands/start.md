# /start $ARGUMENTS

Open the MewVault workspace overview. Optionally drill into a silo or project.

Parse `$ARGUMENTS`:
- Empty → vault overview
- One word (e.g. `design`) → silo drill-in
- Two words (e.g. `design acme-rebrand`) → project drill-in

---

## Step 1 — Vault overview (always run first)

Scan the workspace. For each silo, collect:
- **wiki**: count files in `wiki/_inbox/` (excluding `.gitkeep` and `originals/`)
- **design**: count projects in `design-studio/` (dirs containing `Project_Status.md`)
- **software**: count projects in `software-projects/`
- **games**: count dirs in `game-lab/` (excluding `_experiments/`)

Display:

```
MewVault — YYYY-MM-DD

  wiki      • N inbox items pending        (or: no pending items)
  design    • N active UX project(s)       (or: –)
  software  • N active code project(s)     (or: –)
  games     • N active game project(s)     (or: –)
```

---

## Step 2 — Unwrap detection

For every `Project_Status.md` found across all silos: if `last_session` is newer than `last_wrap`, the previous session ended without `/wrap`.

If any unwrapped sessions found, surface (non-blocking):

```
⚠ Last session didn't wrap cleanly (<project>, <last_session date>).
  Resume there first? Or continue — just say so.
```

Do not block. User can ignore this and keep going.

---

## Step 3 — Silo drill-in (if silo arg given)

Map arg → silo folder:
- `wiki` → `wiki/`
- `design` / `ux` → `design-studio/`
- `software` / `code` → `software-projects/`
- `games` / `game` → `game-lab/`

**wiki silo:**
- Show inbox count and file names
- List open learning paths (`wiki/learning/*/Learning_Path.md` with `status: active`)
- List recent concepts (last 3 modified files in `wiki/concepts/`)

**design silo:**
List every project (`design-studio/*/Project_Status.md`):
```
  <name>   phase <N> <phase-name>   <phase_status>   <days since last_session>
```
Phase names: 0=discovery, 1=analysis, 2=synthesis, 3=audit, 4=ui, 5=handoff

**software silo:**
List every project with `status`, `next_action` (first 60 chars), days since `last_session`.

**games silo:**
List game projects and experiments under `_experiments/`.

---

## Step 4 — Project drill-in (if silo + project arg given)

Find `<silo>/<project>/Project_Status.md`. Read it fully. Display:

```
Project: <name>
Phase: <N> — <phase-name>  |  <phase_status>    (UX projects only)
Last wrap: <last_wrap>

Next action: <next_action>

Open questions:
  - <each item in open_questions[]>     (skip if empty)

Blockers:
  - <each item in blockers[]>           (skip if empty)

In-flight proposals:                    (code projects only)
  - <each dir in proposals/active/>
```

For code projects, also list any `proposals/active/*/status.yaml` — surface `feature`, `tier`, `status` fields.

End with: **"Ready to continue. What are we working on?"**

---

## Rules

- Read-only. Write nothing during `/start`.
- Never auto-process `wiki/_inbox/`. Report count only.
- Recovery offer is non-blocking.
- If the project or silo arg doesn't match anything, list available options and ask.
