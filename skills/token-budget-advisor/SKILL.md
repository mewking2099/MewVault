---
name: token-budget-advisor
description: Use when the user wants to control response length, depth, or token budget. Trigger on "token budget", "short version", "brief answer", "respond at 50%", or any explicit request to control answer size.
origin: ECC
---

# Token Budget Advisor

Intercept the response flow to offer the user a choice about response depth **before** answering.

## When to Trigger

- User mentions "token budget", "token count", "response length", "how many tokens"
- User says "short version", "brief answer", "tldr", "exhaustive answer"
- User says "respond at 50%", "give me the 25% version", "dame la version corta"
- Any request to explicitly control answer size or depth

**Do NOT trigger when:**
- User already set a depth level earlier in this session (maintain it silently)
- The answer is trivially one line
- "Token" refers to auth/session/payment tokens, not response size

## How It Works

### Step 1: Estimate input tokens

- Prose: `words × 1.3`
- Code-heavy content: `chars ÷ 4`

### Step 2: Estimate response window by complexity

| Complexity | Multiplier | Examples |
|------------|-----------|----------|
| Simple | 3×–8× | "What is X?", yes/no |
| Medium | 8×–20× | "How does X work?" |
| Medium-High | 10×–25× | Code request with context |
| Complex | 15×–40× | Multi-part analysis, architecture |

Response window = `input_tokens × mult_min` to `input_tokens × mult_max`

### Step 3: Present depth options

```
Analyzing your prompt...

Input: ~[N] tokens  |  Type: [prose/code/mixed]  |  Complexity: [level]

Choose your depth level:

[1] Essential   (25%)  →  ~[N] tokens   Direct answer only
[2] Moderate    (50%)  →  ~[N] tokens   Answer + context + 1 example
[3] Detailed    (75%)  →  ~[N] tokens   Full answer with alternatives
[4] Exhaustive (100%)  →  ~[N] tokens   Everything

Which level? (1–4 or say "25% depth")

Precision: heuristic estimate, ~85–90% accuracy (±15%).
```

### Step 4: Respond at chosen level

| Level | Length | Include | Omit |
|-------|--------|---------|------|
| 25% Essential | 2–4 sentences | Direct answer, key conclusion | Context, examples, nuance |
| 50% Moderate | 1–3 paragraphs | Answer + context + 1 example | Deep analysis, edge cases |
| 75% Detailed | Structured response | Multiple examples, alternatives | Extreme edge cases |
| 100% Exhaustive | No restriction | Everything | Nothing |

## Shortcuts

If the user already signals a level, respond at that level immediately without asking:

| Signal | Level |
|--------|-------|
| "1" / "brief" / "tldr" / "short version" | 25% |
| "2" / "moderate" / "balanced" | 50% |
| "3" / "detailed" / "thorough" | 75% |
| "4" / "exhaustive" / "full deep dive" | 100% |

If a level was set earlier in the session, **maintain it silently** for all subsequent responses.
