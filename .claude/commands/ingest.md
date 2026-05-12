# Ingest

Read a source document and distill it into structured concept pages — with discussion before writing.

## Arguments

`$ARGUMENTS` is the path to the source document (relative to the current silo's `raw/` directory, or an absolute path).

## Steps

**1. Locate document**

If `$ARGUMENTS` is empty, list files in the current silo's `raw/` directory and ask which to ingest.

Read the document. If it's large (>500 lines), read in sections.

**2. Discuss before writing** (Karpathy rule — mandatory)

Do NOT write any files yet. Instead:

Propose a set of concept pages to extract:
```
I'd extract these concept pages from this document:

1. **<Title>** — <one-line description of what this page would cover>
2. **<Title>** — <one-line description>
...

Does this breakdown look right? Any to add, remove, or merge?
```

Wait for the user's response. Revise the list if asked.

**3. Write concept pages** (only after approval)

For each approved concept page, write to the current silo's `wiki/<slug>.md` using the Concept Page template:
```markdown
---
title: <Title>
source: raw/<filename>
date: <today>
type: concept
---
# <Title>

## Summary
<2-4 sentence distillation>

## Key points
- <point 1>
- <point 2>
...

## Related
[[<related concept>]]
```

Reference the source document: `(source: raw/<filename>)` at the bottom.

**4. Update mewwiki Knowledge index immediately**

Read the mewwiki path from `mewvault/.mewwiki`. Append to `mewwiki/Knowledge/index.md` under `## Concepts`:
```
- [[Knowledge/concepts/<slug>|<Title>]] — <one-line description> · (via <silo>/<project>, <date>)
```

Note: the concept pages themselves will flow to `mewwiki/Knowledge/concepts/` on the next `mew wiki sync`. The index entry is created immediately.

**5. Confirm**

```
Ingested: <filename>
Concept pages written: <N>
  - <silo>/wiki/<slug>.md
  ...
Knowledge index: updated
Sync: concept pages will appear in mewwiki/Knowledge/ on next mew wiki sync
```
