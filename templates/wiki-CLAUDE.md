# Silo: wiki — Second Brain

Obsidian vault root. Knowledge, learning, decisions, references, daily capture.

## Taxonomy (fixed — no new top-level folders)

| Folder | Purpose |
|---|---|
| `_inbox/` | Raw drops awaiting processing — never auto-process |
| `concepts/` | Atomic evergreen notes |
| `projects/` | Project-linked notes |
| `learning/` | Learning paths, sessions, registries |
| `decisions/` | Global ADRs |
| `references/` | External citations, papers |
| `daily/` | YYYY-MM-DD.md quick capture — excluded from inbox flow |

## Frontmatter schema

```yaml
---
title: <title>
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: concept | project-note | learning | decision | reference
tags: []
links: []
status: draft | reviewed | evergreen
source: <_inbox path>
promoted_from: null
promoted_to: []
confidential_source: null
---
```

## NotebookLM integration

NotebookLM is an upstream tool — use it for absorbing dense source material. Export summaries and notes to `_inbox/`. "process the inbox" routes them:
- Study notes / summaries → `learning/<topic>/` (merge with session notes)
- Concept extracts → `concepts/<topic>/` (new or existing note)
- Reference docs → `references/`

When routing NotebookLM exports to a learning track, append the source to `learning/<topic>/resources.md`.

## Rules

- "process the inbox" trigger only — never auto-process `_inbox/`.
- PDFs: Docling extracts to markdown first; original moves to `_inbox/originals/`.
- `web_research: true` must be set explicitly before any web augmentation.
- `daily/` notes are not part of the inbox flow — promote keepers weekly.
- Every note that references a project links to that project's hub.
