---
name: code-review
triggers: [review, check this, look at this code, is this correct, code quality]
description: Security and quality review of changed files
inject: on-trigger
claude_code_skills: [differential-review, static-analysis]
---

# Skill: Code Review

Review changed files for:

**Security (check all):**
- SQL injection (raw string interpolation into queries)
- XSS (unescaped user input in HTML/JSX)
- Command injection (user input in shell commands)
- Hardcoded secrets or API keys
- Insecure direct object references

**Quality:**
- Functions longer than 40 lines (consider splitting)
- Deeply nested conditionals (> 3 levels)
- Magic numbers without named constants
- Error paths that silently swallow exceptions
- Missing null/undefined guards at system boundaries

**Output format:**
```
## Review: <filename>
Severity: critical / warning / suggestion
- <finding>
```

If no issues found: "✓ No issues found in <filename>."
