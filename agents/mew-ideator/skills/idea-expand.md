---
name: idea-expand
triggers: [expand this idea, flesh out, what if, deepen, explore angles]
description: Deepen a seed idea by surfacing the real problem, specific user pain, pivot angles, analogous products, and moats. Modifies idea.md in-place. Use when an idea is captured but thin — user wants to think it through before validating.
inject: on-trigger
---

# Skill: Idea Expand

Take a thin seed and make it worth researching.

## When you're here

The idea exists but idea.md is shallow — the problem is vague, the target user is generic, or the differentiation is unclear. Your job is structured thinking, not research. You're reasoning from what's known to sharpen what matters before feasibility-scan goes to verify it.

Don't fetch data or run web searches here — that's feasibility-scan's domain. Think first, research second.

## Step 1 — Identify the idea

If inside `idea-hub/ideas/<slug>/`, use that. Otherwise ask for the slug.

Read `idea-hub/ideas/<slug>/idea.md`.

## Step 2 — Deepen the problem

Push the Problem and Target User sections past their first draft. For each question below, add what you can infer from the idea — don't ask the user to answer these, reason through them:

- **Who, specifically?** Narrow the target user to a job title, context, or trigger event. Not "developers" — "solo founders shipping their first SaaS without a PM".
- **What do they do today?** Name the current workaround or closest alternative they're stuck with.
- **What does it cost them?** Time, money, or frustration — make it concrete.
- **When does the problem hit?** What triggers it?

Rewrite or expand the Problem and Target User sections in idea.md with what you find. Improve what's there — don't delete it.

## Step 3 — Surface pivot angles

List 3 alternative framings of the same core insight. These aren't better ideas — they're different bets on which form of the problem is worth solving.

Format as a new `## Pivot Angles` section in idea.md:
```markdown
## Pivot Angles
- **[Framing A]**: [one sentence — what changes about scope, user, or distribution]
- **[Framing B]**: ...
- **[Framing C]**: ...
```

Good pivots change one axis: who you serve, how it's delivered, or what part of the workflow you own.

## Step 4 — Map analogous products

Find 3–5 products from adjacent markets that solved a structurally similar problem. These aren't competitors (feasibility-scan covers those) — they're proof that people paid for something with the same underlying mechanism.

The analogy is about structure, not surface. If the idea is "async video feedback for design reviews", the analogies might be Loom (async communication replacing sync meetings), Linear (async structured review replacing Jira chaos), or Loom+Notion (async reference over live discussion). Not Figma.

Add a `## Analogous Products` section:
```markdown
## Analogous Products
| Product | Market | What they proved |
|---------|--------|-----------------|
| ...     | ...    | ...             |
```

## Step 5 — Identify the moat

What would make this defensible once someone copies it? Pick the realistic moat(s) for this idea:

- **Network effect** — more users = more valuable for everyone
- **Data flywheel** — usage generates data that improves the product
- **Switching cost** — users would lose meaningful work by leaving
- **Workflow lock-in** — embedded in a daily process that's painful to change
- **Brand** — trusted authority in a specific domain
- **None yet** — honest answer for most early seeds

Add a `## Moat` section:
```markdown
## Moat
<chosen moat(s) and a sentence on why this idea has a path to it>
```

If the honest answer is "none yet", say that. A defensibility gap is a real finding.

## Step 6 — Update status and chain

Check the `seed → exploring` gate requirements:
- Clear problem statement ✓/✗
- Identified target user ✓/✗
- Rough effort estimate ✓/✗ (this one stays missing — flag it)

If problem + target user are now solid:
- Update `status.md`: change `stage: seed` to `stage: exploring`
- Add to Stage History: `- **<today>** — exploring — problem defined via idea-expand`
- Update `status.md` frontmatter: `updated: <today>`
- Update `idea-hub/Project_Status.md`: decrement `seed_count`, increment `exploring_count`

If problem or target user is still too vague after expansion, keep stage as `seed` and note what's still missing.

Report what changed, then:

"Next: run `feasibility-scan` to validate market size, competitors, and solo viability. Or add an effort estimate first if you want to move to `exploring`."
