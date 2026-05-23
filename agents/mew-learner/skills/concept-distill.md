---
name: concept-distill
triggers: [distil, distill, concept, summarise, summarize, key ideas, take notes on, what are the main points]
description: Distil a source document into structured concept pages
inject: on-trigger
---

# Skill: Concept Distil

When given a document, article, or raw source to distil:

1. Read it fully.
2. Present 5–10 key ideas: name, one-sentence summary, related existing concepts.
3. **Wait for the user to confirm** before writing anything.
4. For each confirmed concept, write a page at `Knowledge/concepts/<slug>.md`:

```markdown
---
title: <Concept Name>
source: raw/<file>
date: YYYY-MM-DD
type: concept
---

# <Concept Name>

## Summary
<2–3 sentences>

## Key points
- <point>

## How it connects
- [[related-concept]] — <why related>

## Source quote
> <most important quote from source>
```

5. Update `Knowledge/index.md` with a link to each new page.
6. Never create a concept page that duplicates an existing one — update instead.
