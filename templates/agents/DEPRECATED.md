# DEPRECATED — templates/agents/

This directory is superseded by `agents/*/system-prompt.md`.

As of agent-array-v2, each agent's system prompt lives in:

```
agents/<name>/system-prompt.md
agents/<name>/manifest.yaml
agents/<name>/skills/*.md
```

These files are kept as a fallback for `mew agent invoke` (read if `agents/` dir
is missing or the new structure is incomplete). They will be deleted in the
next cleanup pass once the migration is confirmed stable.

To migrate: compare any file here against the matching `agents/<name>/system-prompt.md`.
