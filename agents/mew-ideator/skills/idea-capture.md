---
name: idea-capture
triggers: [capture idea, new idea, brain dump, i have an idea, quick idea]
description: Take a rough prompt or brain dump and scaffold a structured idea.md in idea-hub/ideas/<slug>/. Use whenever the user describes a new idea, mentions wanting to capture something, or dumps raw thoughts — even if they don't say "capture idea" explicitly.
inject: on-trigger
---

# Skill: Idea Capture

Turn a brain dump into a structured seed idea in the idea-hub.

## When you're here

The user has an idea that needs to be captured before it evaporates. Extract signal from noise, scaffold the folder, and leave the idea in a state where it can be developed further. Don't fully flesh it out here — that's idea-expand's job.

## Step 1 — Extract the seed

From the user's message, pull out what you can:
- **Problem**: what pain or gap they're describing (even if vague)
- **Solution**: what they're proposing, roughly
- **Target user**: who has this problem (if mentioned)
- **Differentiation**: what makes this different (if any signal)

If the problem is completely missing, ask one question to surface it. One question — don't interrogate.

## Step 2 — Suggest a slug

Propose a kebab-case slug from the core concept (2–4 words, lowercase). Examples: `async-feedback-tool`, `solo-habit-tracker`, `voice-note-organiser`.

Say: `Slug: \`<slug>\` — confirm or give me a different name.`

Wait for confirmation before writing anything.

## Step 3 — Scaffold the idea folder

After slug is confirmed, create:

```
idea-hub/ideas/<slug>/
├── idea.md     ← filled from template
└── status.md   ← stage: seed
```

**idea.md** — fill from `idea-hub/templates/idea.md.tmpl`. Replace all `{{placeholders}}`:
- `slug` → confirmed slug
- `name` → human-readable title (title-case the slug words)
- `date` → today's date (YYYY-MM-DD)
- Fill Problem, Solution, Target User, Differentiation from Step 1.
- Open Questions → bullet list of what's still unknown. Every seed has some.
- Next Step → "Run idea-expand to deepen the problem definition."

**status.md** — create fresh:

```markdown
---
slug: <slug>
stage: seed
created: <today YYYY-MM-DD>
updated: <today YYYY-MM-DD>
---

# Status: <name>

## Stage History
- **<today>** — seed — captured from brain dump

## Decision Log
(empty — add decisions as the idea develops)
```

## Step 4 — Update Project_Status.md

In `idea-hub/Project_Status.md`, increment:
- `active_ideas` by 1
- `seed_count` by 1

## Step 5 — Confirm and chain

Report:
```
Captured: idea-hub/ideas/<slug>/
  idea.md ✓
  status.md ✓
```

Then ask: "Want me to run idea-expand now to deepen the problem and surface analogous products?"

## What not to do

- Don't fire multiple clarifying questions before capturing — extract what you can and write. Unknown things belong in `Open Questions` in idea.md, not in the conversation.
- Don't create `feasibility.md` yet — that's for the `exploring` stage.
- Don't assign a verdict or score — just capture.
