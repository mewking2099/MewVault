---
name: doc-coauthoring
triggers: [help me write, draft a doc, write a spec, write a proposal, co-author, write a plan, help me write the plan, write this up]
description: Guide users through a structured 3-stage workflow for co-authoring documentation — proposals, specs, MewKing plans, decision docs. Use when the user wants to write any substantial structured document.
inject: on-trigger
claude_code_skills: []
source: anthropics/skills
---

# Doc Co-Authoring Workflow

Structured 3-stage workflow: Context Gathering → Refinement & Structure → Reader Testing.

## When to offer this workflow

Offer the workflow when the user wants to write:
- MewKing plan.md files
- Technical specs or decision docs
- Proposals or PRDs
- Project briefings

Explain the three stages. Ask if they want the structured workflow or prefer to work freeform. If they decline, work freeform.

## Stage 1 — Context Gathering

**Goal:** Close the gap between what the user knows and what Claude knows.

Ask for meta-context:
1. What type of document is this?
2. Who's the primary audience?
3. What's the desired impact when someone reads it?
4. Is there a template or specific format to follow?
5. Any constraints to know?

Then encourage an info dump — all background, context, why alternatives aren't being used, organisational dynamics, timeline pressures. Tell them not to organise it first.

**During context gathering:**
- If the user mentions channels or docs: ask them to paste relevant content
- Track what's known and what's still unclear

After the dump, ask 5–10 numbered clarifying questions based on gaps.

**Exit condition:** Enough context to ask about edge cases and trade-offs without needing basics explained.

## Stage 2 — Refinement & Structure

**Goal:** Build the document section by section through brainstorming and iteration.

### Structure first
If doc structure is clear: ask which section to start with. Suggest starting with the section with the most unknowns (core proposal, technical approach). Leave summary sections for last.

If structure is unclear: suggest 3–5 sections appropriate for the doc type.

Once agreed: create the document file with placeholder text for all sections.

**MewVault**: Write to the appropriate path:
- MewKing plan → `proposals/active/<feature>/plan.md`
- Decision doc → `wiki/<slug>.md` in the relevant silo
- Proposal → `proposals/active/<feature>/brief.md`

### For each section

**Step 1 — Clarifying questions**: Ask 5–10 specific questions about what to include.

**Step 2 — Brainstorm**: Generate 5–20 options to include. Look for context that may have been forgotten.

**Step 3 — Curation**: Ask which to keep/remove/combine. Accept shorthand ("keep 1,4,7").

**Step 4 — Gap check**: Anything important missing?

**Step 5 — Draft**: Write the section. Replace the placeholder using str_replace (never reprint the whole doc).

**Step 6 — Iterate**: Apply feedback surgically. After 3 iterations with no major changes, ask if anything can be removed.

### Near completion
When 80%+ of sections are done: re-read the full document and check for flow, redundancy, contradictions, and filler.

## Stage 3 — Reader Testing

**Goal:** Verify the document works for readers who weren't in this conversation.

Generate 5–10 questions a reader would realistically ask. Spawn a sub-agent with only the document content and test each question.

If the sub-agent gets answers wrong or surfaces gaps: loop back to refinement for those sections.

**Exit condition:** Sub-agent consistently answers correctly with no new gaps surfaced.

## Final review

When reader testing passes:
1. Recommend the user do a final read-through — they own this document
2. Suggest fact-checking any technical details or links
3. Ask if they want one more review pass

## Writing principles

- Be direct and procedural — don't try to sell the workflow
- If user wants to skip a stage: let them
- Use `str_replace` for all edits — never reprint the whole document
- One paragraph per idea; every sentence should carry weight
- Remove anything that wouldn't confuse a reader if deleted
