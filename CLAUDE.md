# Silo: mewvault — CLI Engine

This silo contains the `mew` CLI: entry point, commands, templates, and secrets.

## Structure

- `mew.py` — entry point (`python mew.py <command>`)
- `mew/` — Python package (commands, workspace detection, utilities)
- `mew/memory_store.py` — SQLite FTS5 adapter for cross-session memory
- `mew/commands/memory.py` — `mew memory sync|search|recall|purge`
- `templates/` — scaffolding templates per project type
- `secrets/` — gitignored, owner-only permissions
- `.mew-memory.db` — gitignored SQLite memory store (auto-created on first sync)

## Development rules

- Python 3.11+. Use `pathlib.Path` for all file operations — no hardcoded POSIX paths.
- Cross-platform: Mac and Windows. File permission hardening uses `icacls` on Windows, `chmod 0600` on Unix.
- Never echo secret values. Never commit `secrets/*.env`.
- Keep each command in its own file under `mew/commands/`.
- Templates use `{{placeholder}}` syntax — double curly braces.

## Running

```bash
python mew.py help
python mew.py init
python mew.py status --quick
```

Or install editably: `pip install -e .` → `mew help`
