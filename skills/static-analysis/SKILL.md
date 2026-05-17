---
name: static-analysis
description: Run Semgrep static analysis scan on a codebase to find security vulnerabilities, bugs, and code quality issues. Use when asked to scan for vulnerabilities, run a security audit, perform static analysis, or find bugs across a codebase.
origin: trailofbits
---

# Static Analysis (Semgrep)

Run a Semgrep scan with automatic language detection to surface security vulnerabilities and bugs.

## When to Use

- Security audit of a codebase before release
- Finding vulnerabilities before code review
- Scanning for known bug patterns (injection, auth bypass, unsafe deserialization)
- First-pass analysis after a dependency upgrade

## When NOT to Use

- Binary analysis
- You already have CI Semgrep configured and just want to read results
- You need cross-file taint tracking without Semgrep Pro → use CodeQL instead

## Key Rules

1. **Always use `--metrics=off`** — Semgrep sends telemetry by default. Every command must include this flag.
2. **Present scan plan before running** — state exact rulesets and target, wait for explicit "yes" before executing.
3. **Check for Semgrep Pro** — Pro enables cross-file taint tracking (~250% more true positives):
   ```bash
   semgrep --version 2>&1 | grep -i pro
   ```

## Workflow

### Step 1: Detect language(s)
```bash
find . -name "*.ts" -o -name "*.py" -o -name "*.go" -o -name "*.rs" | head -20
```

### Step 2: Present scan plan
```
Scan plan:
- Target: ./src/
- Rulesets: p/security-audit + p/secrets + trail-of-bits rules
- Engine: Semgrep [Pro if available]
- Mode: important-only (high-confidence findings)

Proceed? [y/n]
```

### Step 3: Run scan
```bash
semgrep scan \
  --config p/security-audit \
  --config p/secrets \
  --metrics=off \
  --sarif \
  --output results.sarif \
  ./src/
```

### Step 4: Parse and report

Group findings by severity (CRITICAL → HIGH → MEDIUM → LOW). For each finding:
- File and line number
- Rule ID and description
- Suggested fix (if rule provides one)
- False positive likelihood

### Step 5: Triage

For each HIGH/CRITICAL finding, verify exploitability:
- Is the tainted input reachable from user-controlled data?
- Is there existing validation upstream?
- What is the impact if exploited?

Output a prioritized list: fix now / fix before release / monitor / likely false positive.
