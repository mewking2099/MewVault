---
name: competitor-map
triggers: [competitor map, who else does this, competitors, competitive landscape, market map]
description: Structured competitive landscape for an idea or market — positioning, gaps, entry angle. Use whenever the user wants to understand who already plays in a space, even outside the idea-hub lifecycle.
inject: on-trigger
---

# Skill: Competitor Map

Map who else plays in this space and where the gaps are.

## When you're here

The user wants to understand competitive landscape — either for an idea in the hub, or for a market they're curious about. This skill works standalone (no idea folder needed) or as part of feasibility research. The goal isn't just a list of competitors — it's identifying the gap that makes an entry angle real.

## Research tools

**Default**: WebSearch + WebFetch.

**Extended** (use if available): NotebookLM or Gemini for synthesis. Fall back to web if unavailable.

## Step 1 — Define the space

If context is an existing idea, read `idea-hub/ideas/<slug>/idea.md` for the problem + solution.

Otherwise: "What's the problem space? One sentence — what does the ideal product do for who?"

Don't start searching until you can name the space clearly.

## Step 2 — Find competitors

Search for 5–10 players using varied queries:
```
"[solution type] tool OR platform OR app"
"[problem] software"
"best [solution category]"
"alternatives to [most obvious tool]"
"[problem] [target user] site:reddit.com OR site:producthunt.com"
```

ProductHunt and Reddit are high-signal for real usage patterns — prioritise them over pure SEO-ranked listicles. Real complaints in Reddit threads often name what's broken about existing tools, which is more useful than any vendor's marketing copy.

## Step 3 — Build the map

For each competitor:
- **Name + URL**
- **What they do** (1 sentence, from their own framing — not your interpretation)
- **Pricing** (free / freemium / paid — rough tier)
- **Their gap** — what they don't solve well (this column is the most important)

Format:
```markdown
## Competitor Map — <space name>

| Name | What they do | Pricing | Gap |
|------|-------------|---------|-----|
| ...  | ...         | ...     | ... |

## Positioning Summary
<2–3 sentences on how the space is segmented — enterprise vs solo, async vs real-time, 
horizontal vs vertical, open-source vs SaaS.>

## Entry Angle
<The gap sentence: "No one currently does X well for Y type of user.">
```

If you can't write the Entry Angle, the research isn't complete. Keep searching.

## Step 4 — Deliver or append

If standalone: present the map in conversation.

If working on an idea from the hub: "Want me to paste this into `idea-hub/ideas/<slug>/feasibility.md` under the Competitors section?"
