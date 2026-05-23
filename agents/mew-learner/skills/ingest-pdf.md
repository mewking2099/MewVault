---
name: ingest-pdf
triggers: [ingest, read this pdf, process this document, extract from, import this]
description: Process a raw PDF or document into wiki concept pages
inject: on-trigger
---

# Skill: Ingest PDF / Document

When the user provides a file path to ingest:

1. Confirm the file is in a `raw/` directory (immutable — read only).
2. Read the file. For PDFs, use the Read tool with `pages` parameter for large files.
3. Identify document type: spec / research paper / meeting notes / reference doc.
4. Run the **concept-distill** skill workflow on the extracted content.
5. Store the original file reference in the concept page frontmatter: `source: raw/<file>`.

**Special handling:**
- **PRDs / specs** → also produce a `proposals/active/<feature>/plan.md` outline
- **Meeting notes** → route to `Operations/Meetings/` not `Knowledge/concepts/`
- **API docs** → route to `Knowledge/concepts/` with `type: api-note`

Never delete or move files in `raw/`.
