# Code Reviewer

A structured code review skill for any diff or PR. Adapted from the ECC code-reviewer agent pattern.

## When to use

- Before merging a MewKing feature
- When the user asks for a code review
- As part of the verification loop for large changes

## Review checklist

### Correctness
- Does the code do what it claims? Walk through the main logic path.
- Are edge cases handled? (empty input, null, overflow, concurrent access)
- Are error cases handled at the right layer?

### Security
- No secrets in code or comments
- No SQL injection, XSS, or command injection vectors
- No insecure deserialization
- Input validation at system boundaries only (not deep in internal functions)

### Architecture
- Does this change fit the existing patterns in the codebase?
- Are abstractions at the right level? (not too early, not too late)
- Are new dependencies justified?

### Tests
- Are new behaviors covered by tests?
- Do existing tests still pass after this change?
- Are tests testing behavior, not implementation?

### Readability
- Are names clear and consistent with the codebase conventions?
- Is any comment explaining WHY (not WHAT)?
- Is anything dead code or unused?

## Output format

```
## Review: <file or feature>

**Verdict**: Approve / Request changes / Needs discussion

**Issues**
- [BLOCKER] <description>
- [MINOR] <description>
- [NIT] <description>

**Questions**
- <anything unclear that warrants discussion>

**Positives**
- <what was done well>
```

## Rules

- BLOCKER = must fix before merge
- MINOR = should fix, but not a blocker
- NIT = style or preference, take it or leave it
- If no issues, say so explicitly — an empty issues list is a valid review outcome.
