---
name: idea-brief
triggers: [idea brief, one-pager, pitch this, summarise idea, summarize idea]
description: Produce a one-page pitch summary (brief.md) from an idea folder. Use when the user wants to present, share, or pitch an idea — even if they just say "summarise this idea" or "give me a one-pager for X".
inject: on-trigger
---

# Skill: Idea Brief

Distil an idea folder into a scannable one-page pitch.

## When you're here

The user wants to communicate an idea to someone else — or to themselves, clearly. The brief synthesises idea.md + feasibility.md (if available) into something a stakeholder can read in 60 seconds. It's a deliverable, not a conversation — it goes into a file.

## Step 1 — Identify the idea

If inside `idea-hub/ideas/<slug>/`, use that.

Otherwise ask: "Which idea? Give me a slug or name."

## Step 2 — Read the source files

Read in order, skip if missing:
1. `idea-hub/ideas/<slug>/idea.md` — required
2. `idea-hub/ideas/<slug>/feasibility.md` — optional (adds market signal + verdict)
3. `idea-hub/ideas/<slug>/status.md` — for current stage

If idea.md still has unfilled `{{placeholder}}` values, stop and tell the user: "idea.md has unfilled sections. Run idea-capture or idea-expand first to populate it."

## Step 3 — Write brief.md

Write to `idea-hub/ideas/<slug>/brief.md`:

```markdown
---
slug: <slug>
generated: <today YYYY-MM-DD>
stage: <from status.md>
---

# <Name>
> <one-sentence tagline — the clearest possible description of what this is>

## The Problem
<2 sentences. Who has it, what it costs them — specific, not generic.>

## The Solution
<2 sentences. What this makes possible. No jargon, no buzzwords.>

## Target User
<1 sentence, specific. Not "developers" — "solo founders shipping their first SaaS who can't afford a PM".>

## Why This / Why Now
<What makes this different from the obvious alternatives. A real differentiator — not "it's simpler" or "it's better".>

## Market Signal
<If feasibility.md exists: rough market size, verdict (green/amber/red), key competitor gap.>
<If not: "(no feasibility data yet — run feasibility-scan to add this)">

## Biggest Risk
<The one thing most likely to kill this. Be honest — a real risk, not a placeholder.>

## Status
Stage: <seed / exploring / validated>
Next step: <from idea.md's Next Step field>
```

Keep every section tight. This is a pitch, not a spec. If you're unsure about a section, write what you know and mark uncertain bits with `(?)`.

## Step 4 — Report

```
Written: idea-hub/ideas/<slug>/brief.md
```

No chaining — this is a terminal deliverable.
