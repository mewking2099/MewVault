---
name: variant-analysis
description: Find similar vulnerabilities and bugs across a codebase after identifying an initial pattern. Use when hunting bug variants, building CodeQL/Semgrep queries, or performing systematic audits after finding one instance of an issue.
origin: trailofbits
---

# Variant Analysis

Find every instance of a known bug or vulnerability pattern across a codebase.

## When to Use

- A vulnerability was found — search for similar instances before reporting
- Building CodeQL/Semgrep rules for a known pattern
- Systematic code audit after an initial issue discovery
- Proving scope of a bug class (how many files are affected?)

## When NOT to Use

- Initial vulnerability discovery (use `static-analysis` first)
- General code review without a known pattern
- Writing fix recommendations

## Five-Step Process

### Step 1: Understand the original issue

Before searching, answer:
- **Root cause:** WHY is it vulnerable (not just what)
- **Required conditions:** Control flow, data flow, state
- **What makes it exploitable:** User-controlled input, missing validation, etc.

### Step 2: Create an exact match

Start with a pattern that matches ONLY the known instance:
```bash
rg -n "exact_vulnerable_code_here" --type ts
```
Verify: does it match exactly one location?

### Step 3: Identify abstraction points

| Element | Keep specific | Can abstract |
|---------|--------------|--------------|
| Function name | If unique to bug | If family of functions |
| Variable names | Never | Always (use `$VAR`) |
| Literal values | If value matters | If any value triggers bug |
| Arguments | If position matters | Use `...` wildcards |

### Step 4: Iteratively generalize

Change ONE element at a time:
1. Run the generalized pattern
2. Review ALL new matches
3. Classify: true positive or false positive?
4. Accept if FP rate < 50%; otherwise revert and try different abstraction

```bash
# Ripgrep for simple patterns
rg -n "pattern" --type py

# Semgrep for structural patterns
semgrep --pattern '$X.execute($QUERY)' --lang python --metrics=off .
```

### Step 5: Triage results

For each match:
- **Location:** file, line, function
- **Confidence:** High / Medium / Low
- **Exploitability:** Is user input reachable? Is it controllable?
- **Priority:** Impact × exploitability

Output a table: file | line | confidence | notes.
