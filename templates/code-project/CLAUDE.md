# Project: {{name}} — Code

Stack: {{stack}}
Started: {{date}}

## What to read first

1. `Project_Status.md` — current focus, open questions
2. `proposals/active/` — any in-flight MewKing features (check `status.yaml`)
3. `decisions/` — prior architectural decisions
4. `docs/ux/` — promoted UX artifacts (if from a design-studio project)

## The Court

Use `/plan <feature>` — Claude proposes Pounce / Stalk / MewKing.
Plan approval gate is at MewKing → Plan stage. Nothing proceeds without sign-off.

## API contract

Document at project root:
- HTTP → `openapi.yaml`
- GraphQL → `schema.graphql`
- CLI → `README.md` Commands section

Update contract at MewKing Finalize stage.
