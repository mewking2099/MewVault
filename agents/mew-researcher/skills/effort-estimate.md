---
name: effort-estimate
triggers: [effort estimate, how long, t-shirt size, how big is this, solo viable]
description: T-shirt size an idea or feature — S/M/L/XL, phase count, stack recommendation, solo-viable flag. Use when the user wants to know how much work something is before committing.
inject: on-trigger
---

# Skill: Effort Estimate

Give a realistic size before the user commits time they don't have.

## When you're here

The user wants a rough effort estimate before deciding whether to pursue something. The goal is calibration, not precision — a wrong T-shirt size costs nothing; an underestimated commitment costs months.

Bias toward honesty. Founders systematically underestimate scope. Your job is to surface real complexity, not validate optimism.

## Step 1 — Define what's being estimated

If it's an idea in the hub, read `idea-hub/ideas/<slug>/idea.md`.

If it's a feature or description in conversation, ask: "What does the MVP need to do? What's explicitly out of scope?"

Don't estimate until you can describe the core user journey in one sentence.

## Step 2 — Break into phases

Identify the natural build phases — things that are each shippable on their own. Typical for software products:

1. **Core loop** — the single thing the product must do to be useful
2. **User-facing shell** — auth, onboarding, basic UI
3. **Persistence + reliability** — data model, error handling, production-grade storage
4. **Distribution surface** — sharing, integrations, notifications
5. **Scale / monetisation** — billing, analytics, multi-user

Not every product needs all phases. Stop where the idea's scope stops. An MVP often needs only phases 1–2.

## Step 3 — Name the hardest part

One thing will blow the estimate if underestimated. Identify it:
- An algorithm that isn't solved by OSS
- An integration with a painful or undocumented API
- Real-time infrastructure (websockets, CRDTs, sync)
- ML that needs training data that doesn't exist yet
- A UX pattern with no good precedent

If the hardest part is a known unknown (you can't scope it without a spike), say so explicitly — that's important information.

## Step 4 — Assign T-shirt size

| Size | Solo calendar time | Typical shape |
|------|--------------------|---------------|
| S    | Days to 2 weeks    | Single workflow, no auth, script or widget |
| M    | 1–3 months         | Core loop + auth + persistence |
| L    | 3–6 months         | Multi-surface, third-party integrations |
| XL   | 6+ months          | Platform, ML, multi-user, compliance |

**Solo-viable**:
- **Yes**: M or smaller, no unsolved hard parts, familiar tech stack
- **With caveats**: L with strong OSS leverage, or needs one specific expertise area
- **No**: XL, or contains a hard part that realistically needs a team or specialist

## Step 5 — Stack recommendation (optional)

Only suggest a stack if the choice materially affects the estimate — wrong stack = added weeks. If the user already has a stack in mind, don't override it.

Good defaults for solo founders:
- Speed to MVP → SvelteKit + Supabase, or Next.js + Supabase
- Data-heavy backend → Python + FastAPI + Postgres
- Real-time → SvelteKit + Partykit or Liveblocks
- Mobile-first → React Native + Expo

## Step 6 — Deliver or append

Present the estimate:
```
Size: M
Solo-viable: Yes
Phases: 3
  1. Core loop (~3 weeks)
  2. Auth + persistence (~2 weeks)
  3. Distribution surface (~2 weeks)
Biggest unknown: [X]
Stack: Next.js + Supabase (fast to MVP, familiar)
```

If working on an idea from the hub: "Want me to add this to `idea-hub/ideas/<slug>/feasibility.md` under Effort Estimate? This also satisfies the effort gate for moving the idea to `exploring` stage."
