# Workspace: MewVault Agentic System

You are working in a federated workspace. Each silo is an independent git repo.

## Commands (only four)

- `/start [silo] [project]` — open vault overview, optionally drill in
- `/wrap`                   — end session, return to vault overview
- `/plan <feature>`         — propose a tier (Pounce/Stalk/MewKing) and execute
- `/teach [topic]`          — enter pedagogical mode for a learning track

## Routing

- Knowledge / research → `wiki/`
- UX projects          → `design-studio/<project>/`
- Code                 → `software-projects/<project>/`
- Games                → `game-lab/<project>/`
- Learning             → `wiki/learning/<topic>/`
- Tooling              → `mewvault/`

## Hard rules

- Never edit files outside the current project root without explicit instruction.
- Never auto-process `wiki/_inbox/` — wait for user trigger ("process the inbox").
- Never write code before `plan.md` is approved (MewKing tier).
- Secrets live only in `mewvault/secrets/`. Never echo them. Never commit them.
- Cross-silo promotes/publishes require explicit `mew` command confirmation.
- PDF processing: always use Docling. Never use Claude's native PDF reader.
- Web browsing: always use the Vercel Labs AI browser agent. Never use Claude in Chrome.

## Where to look first

- Project status: `./Project_Status.md`
- In-flight feature state: `./proposals/active/<feature>/status.yaml`
- Silo conventions: `./<silo>/CLAUDE.md`
- Prior decisions: `./decisions/` or `wiki/decisions/`
