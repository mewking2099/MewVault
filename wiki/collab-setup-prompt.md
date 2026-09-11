# MewVault Collab Setup — Master Prompt

> Paste this entire prompt into a Claude Code session inside your MewVault directory.
> It is idempotent — safe to run even if partially done. Claude will read each file first and skip sections already present.

---

**Prompt to paste:**

---

I'm setting up MewVault for collaborative projects. Mohabbat (my collaborator) has already made these changes on his vault. Apply the same changes to mine. Do all of this now without asking for confirmation.

**Step 1 — vault-rules.md**

Find the file at `~/.claude/rules/mew-common/vault-rules.md`. Read it. If a "Collaborative projects" section is not already present, add the following block immediately before the "Planning gates" section:

```
## Collaborative projects

A project is **collaborative** when its `Project_Status.md` contains a `collaborators` field naming one or more other MewVault users.

### Shared memory rule (critical)
Personal Claude memory is per-user and does not sync across collaborators. For collaborative projects:
- Write architectural decisions to `decisions/` (ADRs) — not personal memory.
- Write distilled knowledge to `wiki/` — not personal memory.
- Keep `log.md` entries dated and self-contained so a collaborator's Claude can read them cold after a `git pull`.
- Personal memory may supplement but the repo files (`decisions/`, `wiki/`, `log.md`) are the authoritative shared brain.

### Session start (collaborative)
Before reading `Project_Status.md`, run `git pull` — the collaborator may have pushed since your last session. Then check GitHub Issues for anything recently assigned or closed before starting new work.

### PR discipline
- Never self-merge a PR on a collaborative project. Every PR requires at least one review from a named collaborator.
- Branch protection enforcing this must be active on the GitHub repo.
```

**Step 2 — code-rules.md**

Find the file at `~/.claude/rules/mew-code/code-rules.md`. Read it. If a "Collaborative projects" section is not already present, add the following block immediately after the "Commits" section:

```
## Collaborative projects

When `Project_Status.md` has a `collaborators` field:

- **Issues first** — open a GitHub Issue before starting any Stalk or MewKing work item. The issue is the shared workqueue; `log.md` is the session narrative.
- **No self-merge** — every PR requires a review from a collaborator before merge. Link PRs to their issue (`Closes #N` in the PR body).
- **ADRs as shared memory** — architectural decisions go to `decisions/<NNNN>-<slug>.md` instead of personal Claude memory, so the collaborator's Claude can read them on next pull.
- **Session wrap addition** — after updating `log.md`, close or comment on any GitHub Issues touched this session.
```

**Step 3 — CLAUDE.md path map**

Find `CLAUDE.md` in the mewvault root. Read the "Known project name → path map" section. If `tendersense` is not already listed, add this line to the map:

```
- `tendersense` / `TenderSense` / `tender-sense` → `software-projects/tendersense` (collaborative: mohabbat)
```

**Step 4 — Clone TenderSense**

Check whether `software-projects/tendersense/` exists locally. If not, remind me to clone it:
```
git clone https://github.com/itsmeshawon/tendersense software-projects/tendersense
```
Do not clone it yourself — just flag it if missing.

**Step 5 — Save a memory**

Save a project memory with these details:
- TenderSense (`software-projects/tendersense`) is a collaborative project with Mohabbat (mewking2099)
- Both collaborators use MewVault
- Shared brain = `decisions/` + `wiki/` + `log.md` in the repo, synced via git pull
- GitHub Issues = shared workqueue
- Branch protection active on `main` — PRs require collaborator review before merge
- Production: https://tendersense-delta.vercel.app
- Phase 0 Foundation ~95% done (auth + workspaces + RLS + deploy verified as of 2026-09-11)
- Next: Session 4 — ADRs 0001–0005, tag v0.1.0-phase0, then Phase 1 source ingestion plan

**Step 6 — Confirm**

After all steps are done, report:
- vault-rules.md: added / already present
- code-rules.md: added / already present
- CLAUDE.md path map: added / already present
- software-projects/tendersense: exists / needs clone
- Memory: saved
