# Secrets Guardian

Secrets are API keys, tokens, passwords, and credentials. They belong only in `mewvault/secrets/`.

## Patterns that trigger a block

The PreToolUse hook blocks writes containing:
- `sk-` prefix (Anthropic, OpenAI keys)
- `ghp_` prefix (GitHub personal access tokens)
- `AKIA` prefix (AWS access key IDs)
- `API_KEY=`, `ANTHROPIC_API_KEY=`, `OPENAI_API_KEY=` assignments
- `password=` or `passwd=` assignments

## Rules

- Never echo a secret in a response, even partially.
- Never commit secrets — `mewvault/secrets/` is gitignored.
- Use `mew secret set KEY_NAME` to store a new secret.
- Use `mew secret get KEY_NAME` to retrieve (environment variable injection, not echo).
- Rotate secrets with `mew secret rotate KEY_NAME`.
