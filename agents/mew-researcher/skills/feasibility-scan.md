---
name: feasibility-scan
triggers: [feasibility, is this viable, validate idea, research this, feasibility scan]
description: Research and assess an idea's market size, competitors, tech complexity, and effort. Writes feasibility.md with a green/amber/red verdict. Use when the user wants to know if an idea is worth building — even if they just ask "is this viable?" or "should I build this?".
inject: on-trigger
---

# Skill: Feasibility Scan

Answer: is this worth building? Research first, verdict second.

## When you're here

The idea is defined enough to research. Your job is to gather real signal — market size, who else plays in this space, tech complexity, solo viability — and then produce a written verdict the user can act on.

Be honest. A red verdict saves months of wasted work. An amber verdict with clear caveats is more useful than an optimistic green that glosses over blockers.

## Research tools

**Default**: WebSearch + WebFetch. Use these for all lookups.

**Extended** (use if available in MCP): NotebookLM for document-grounded research, Gemini for synthesis. Check if these MCPs are wired in — if not, fall back to web search gracefully.

**Manual drop**: The user may paste research results directly into the conversation. If they do, treat that content as source material and cite it as `(source: user-provided)`.

Partial research is better than no research. Work with what's available.

## Step 1 — Identify and check the idea

Ask for the slug if not clear from context.

Read:
- `idea-hub/ideas/<slug>/idea.md` — required
- `idea-hub/ideas/<slug>/status.md` — check stage

If stage is still `seed`, warn: "This idea hasn't been deepened yet — the problem definition may be too vague for useful research. Consider running idea-expand first. Continue anyway?"

## Step 2 — Market research

Search for demand signal:
```
"[core concept] market size"
"[problem] how many people"
"[industry] TAM OR market"
"[problem] reddit OR producthunt"
```

Goal: rough order of magnitude — millions / hundreds of millions / billions / niche. Exact numbers aren't required; trend and signal matter more.

Note demand signals: Reddit threads with real pain, job postings requiring this skill, existing tools with visible user bases.

Cite every factual claim: `(source: URL)`.

## Step 3 — Competitor research

Search for who else plays here:
```
"[solution type] tool OR platform OR app"
"[problem] software"
"best [solution category]"
"alternatives to [closest known product]"
"[problem] [target user] site:reddit.com OR site:producthunt.com"
```

Find 3–7 competitors. For each: what they do, rough pricing tier, and — most importantly — their gap.

The gap is the entry point. "No one currently does X well for Y type of user" is the sentence you're trying to write.

## Step 4 — Tech complexity

Identify the hardest technical part of the solution. Ask:
- Is this a known-solved problem with OSS leverage? (search `"[core tech] open source library"`)
- Does it require real-time infrastructure, ML, proprietary data, or platform-specific APIs?
- Can one developer own the full stack without burning out?

Assign: **low / medium / high** complexity with one-sentence reasoning.

## Step 5 — Effort estimate

T-shirt size:
| Size | Solo calendar time | Typical |
|------|--------------------|---------|
| S    | Days to 2 weeks    | Simple tool, single workflow |
| M    | 1–3 months         | Core loop + auth + persistence |
| L    | 3–6 months         | Multi-surface, integrations |
| XL   | 6+ months          | Platform, ML, multi-team |

Solo-viable: **yes / with caveats / no**
Biggest unknown: the one thing most likely to blow the estimate.

## Step 6 — Form the verdict

- **green** — real market signal, competitors validate demand, solo-viable, no fatal blocker
- **amber** — viable with caveats — list them explicitly. Amber is not a polite red.
- **red** — significant blocker: market too small, problem already solved well, tech complexity beyond solo, no differentiation path

One fatal blocker overrides everything else → red. Be specific about what the blocker is.

## Step 7 — Write feasibility.md

Fill `idea-hub/templates/feasibility.md.tmpl` → write to `idea-hub/ideas/<slug>/feasibility.md`.

Replace all `{{placeholders}}`. Cite sources inline throughout.

## Step 8 — Update status.md

If verdict is **green or amber**:
- Update `stage` to `validated`
- Add to Stage History: `- **<today>** — validated — feasibility scan complete, verdict: <green/amber>`
- Update `status.md` frontmatter: `updated: <today>`
- Update `idea-hub/Project_Status.md`: decrement `exploring_count`, increment `validated_count`

If verdict is **red**:
- Keep stage as `exploring` unless the idea is clearly dead
- Add to Decision Log: `- **<today>** — blocker: <one-line summary>`

## Step 9 — Report and chain

Report:
```
Written: idea-hub/ideas/<slug>/feasibility.md
Verdict: <green / amber / red>
```

If green or amber: "Want to generate a pitch brief? Run `idea-brief` to produce a one-pager."
