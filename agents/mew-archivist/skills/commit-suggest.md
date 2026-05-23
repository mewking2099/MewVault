---
name: commit-suggest
triggers: [commit message, suggest commit, git commit, what should i commit]
description: Generate a conventional commit message from session activity
inject: on-trigger
---

# Skill: Commit Suggest

Generate a conventional commit message from changed files and session activity.

Format:
```
<type>(<scope>): <imperative summary under 72 chars>

- <bullet: what changed>
- <bullet: why, if non-obvious>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Types: `feat` · `fix` · `refactor` · `docs` · `chore` · `test` · `style`

Rules:
- Scope = the project or module (e.g. `wiki`, `agent`, `hooks`, `dsaas`)
- Summary is imperative: "add", "fix", "remove" — not "added", "fixed"
- Only include the Co-Authored-By line for non-trivial changes
- Write to `.claude/last-session-message.txt` — do not run `git commit`
