---
name: doc-coauthoring
triggers: [help me write, draft a doc, write a spec, write this up, write a summary, co-author, write a report, structured document]
description: Guide users through a structured 3-stage workflow for co-authoring any substantial document — session summaries, reports, specs, or decision docs. Use when the user wants structured writing help beyond a simple log entry.
inject: on-trigger
claude_code_skills: []
source: anthropics/skills
---

# Doc Co-Authoring Workflow

Structured 3-stage workflow: Context Gathering → Refinement & Structure → Reader Testing.

## When to offer this workflow

Offer the workflow when the user wants to write:
- Session retrospectives or post-mortems
- Technical writeups or decision records
- Structured summaries (more than a log entry)
- Documentation for external consumption

For simple log entries, use `log-write` instead. For internal session wraps, use `session-wrap`. This skill is for substantial structured documents.

## Stage 1 — Context Gathering

Ask for meta-context:
1. What type of document is this?
2. Who's the primary audience?
3. What's the desired impact?
4. Is there a template or format to follow?

Then encourage an info dump — all relevant context, background, constraints. Tell them not to organise it first.

After the dump, ask 5–10 numbered clarifying questions based on gaps.

**Exit condition:** Enough context to ask about edge cases without needing basics explained.

## Stage 2 — Refinement & Structure

### Structure first
Suggest 3–5 sections appropriate for the doc type. Once agreed: create the file with placeholder text.

**MewVault paths:**
- Session retrospective → `<silo>/<project>/wiki/retro-<date>.md`
- Decision record → `<silo>/<project>/wiki/<slug>.md`
- Report → wherever the user specifies

### For each section

1. **Clarifying questions** (5–10 about what to include)
2. **Brainstorm** (5–20 options)
3. **Curation** (keep/remove/combine — accept shorthand)
4. **Draft** (write the section, use str_replace)
5. **Iterate** (surgical edits only, never reprint full doc)

Near completion: re-read full document for flow, redundancy, and filler.

## Stage 3 — Reader Testing

Generate 5–10 questions a reader would ask. Spawn sub-agent with only the document. Test each question. Loop back to refinement for any gaps found.

**Exit condition:** Sub-agent answers consistently with no new gaps.

## Final review

Recommend user do a final read-through. Check for facts and links. Ask if they want one more pass.

## Writing principles

- Every sentence must carry weight — delete filler
- Use str_replace for all edits, never reprint
- If user wants to skip a stage: let them
