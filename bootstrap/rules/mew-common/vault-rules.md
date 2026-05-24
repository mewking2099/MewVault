# Vault Rules

You are operating inside a MewVault federated workspace. The workspace is split into independent git silos: `wiki/`, `design-studio/`, `software-projects/`, `game-lab/`, and `mewvault/` (tooling).

## File system boundaries

- Never edit files outside the current project root without explicit instruction.
- `raw/` directories anywhere in the workspace are **immutable**. Never write to them.
- `.obsidian/` is off-limits. Obsidian manages its own config.
- Secrets belong only in `mewvault/secrets/`. Never echo, log, or commit them.

## Cross-silo operations

- Cross-silo promotes or publishes require an explicit `mew` command confirmed by the user.
- Never auto-process `wiki/_inbox/` — wait for user trigger ("process the inbox").

## Session discipline

- Every session ends with `/wrap` or `/wrap-up`. Update log.md before closing.
- Every new note needs at least one inbound link before the session ends.
- Every factual claim cites its source: `(source: raw/file.ext)`.

## Planning gates

See tier-gates.md for MewKing, Stalk, and Pounce tier rules.
