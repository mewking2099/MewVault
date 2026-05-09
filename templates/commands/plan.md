# /plan $ARGUMENTS

Plan a piece of work in the current code project. Claude proposes a tier from The Court; you confirm, then the pipeline runs.

`$ARGUMENTS` is the feature description — e.g. "add OAuth login" or "fix typo on pricing page".

---

## Step 1 — Identify project

Confirm the active code project from context, or ask. Find its root at `software-projects/<project>/`. Read `Project_Status.md`.

---

## Step 2 — Assess scope and propose tier

**Heuristics (in order of precedence):**
- Touches auth, billing, payments, encryption, migrations, multi-tenant data, or new subsystems → **MewKing**
- New endpoint, new component, refactor, dependency upgrade, new integration → **Stalk**
- Rename, typo fix, copy change, lint fix, dep bump, config tweak → **Pounce**

State the proposed tier and reasoning in one sentence:
> "This touches the auth system — proposing **MewKing**. Override with 'use stalk' if you disagree."

Wait for confirmation. Accept: "yes", "go", "use pounce", "use stalk", "use mewking", or any clear override.

**Tier escalation rule:** if you believe the user under-tiered, say so before starting and propose escalation. Never silently upgrade.

---

## Step 3 — Auto-inject prior decisions

Before writing anything, grep `decisions/` and the wiki silo's `decisions/` for ADRs whose filename or content matches keywords from the feature description. If found, list them:
> "Prior decisions relevant: [0003-chose-postgres.md], [0007-auth-strategy.md]"

These will be appended as a **Prior Decisions** section in `brainstorm.md` (MewKing) or `plan.md` (Stalk).

---

## Step 4 — Run the tier pipeline

---

### POUNCE

1. **Execute** — make the change directly. No plan file.
2. **Commit** — propose: `"pounce: <description>"`. Do not auto-commit.

---

### STALK

1. **Plan** — write `plan.md` at the project root:

   ```markdown
   # Plan: <feature>

   ## Approach
   <one paragraph — what changes and why>

   ## Files to touch
   - `<path>` — <what changes>
   - `<path>` — <what changes>

   ## Out of scope
   <anything explicitly excluded>

   ## Prior Decisions
   <auto-injected ADRs, or "(none)">
   ```

   Show the plan. Ask: **"Proceed?"** Wait for explicit approval before writing any code.

2. **Code** — implement the changes.

3. **Commit** — propose: `"feat: <description>"`. Do not auto-commit. Delete `plan.md` after commit.

---

### MEWKING

Feature slug: kebab-case of the feature name.
Folder: `proposals/active/<slug>/`

Create `proposals/active/<slug>/status.yaml` immediately:

```yaml
feature: <slug>
stage: brainstorm
plan_approved: false
plan_approved_at: null
review_attempts: 0
last_updated: <ISO timestamp>
created: <ISO timestamp>
```

Update `stage` and `last_updated` in `status.yaml` at every stage transition.

---

#### Stage 1 — Brainstorm

Create `proposals/active/<slug>/brainstorm.md`:

```markdown
# Brainstorm: <feature>

## Option A — <name>
<description and tradeoffs>

## Option B — <name>
<description and tradeoffs>

## Option C — <name>
<description and tradeoffs>

## Prior Decisions
<auto-injected ADRs, or "(none)">
```

Minimum 3 options. Show the file. Ask which option to pursue (or how to combine). Wait.

---

#### Stage 2 — Spec

Update `stage: spec` in `status.yaml`.

Create `proposals/active/<slug>/spec.md`:

```markdown
# Spec: <feature>

## Chosen approach
<one paragraph — from brainstorm decision>

## Behavior
<what the feature does, from the user's perspective>

## Edge cases
- <case> → <expected behavior>

## Success criteria
- [ ] <criterion>
- [ ] <criterion>

## Contract fragment
<OpenAPI YAML fragment, GraphQL schema delta, or "(no interface changes)">
```

Show it. Ask: **"Approve spec?"** Wait. Do not proceed without approval.

---

#### Stage 3 — Plan 🔒 HARD GATE

Update `stage: plan` in `status.yaml`.

Create `proposals/active/<slug>/plan.md`:

```markdown
# Plan: <feature>

## File changes
| File | Action | Notes |
|---|---|---|
| `path/to/file.ts` | modify | <what changes> |
| `path/to/new.ts` | create | <purpose> |

## Migrations
<list DB migrations required, or "(none)">

## Rollback
<how to undo if this needs to be reverted>
```

Show it. Ask: **"Approve plan?"**

**Do not write a single line of code until the user explicitly approves the plan.**

On approval: set `plan_approved: true` and `plan_approved_at: <ISO timestamp>` in `status.yaml`.

---

#### Stage 4 — TDD

Update `stage: tdd` in `status.yaml`.

Write failing tests that encode the spec's success criteria. All tests must be red before moving to Execute.

---

#### Stage 5 — Execute

Update `stage: execute` in `status.yaml`.

Implement until all tests are green. No behavior beyond what the tests cover.

---

#### Stage 6 — Review

Update `stage: review` in `status.yaml`. Increment `review_attempts`.

Create `proposals/active/<slug>/review.md`:

```markdown
# Review: <feature>

## Spec deviations
<list any, or "(none)">

## Test coverage gaps
<list any, or "(none)">

## Verdict
pass | fail
```

- Verdict **pass** → proceed to Finalize.
- Verdict **fail**, `review_attempts <= 2` → loop back to Execute with specific fixes.
- Verdict **fail**, `review_attempts > 2` → escalate to Plan. The plan or spec was wrong, not the code. Do not silently re-spec to match what was built.

---

#### Stage 7 — Finalize

Update `stage: finalize` in `status.yaml`.

1. Merge contract fragment from `spec.md` into the project's contract file (`openapi.yaml`, `schema.graphql`, etc.).
2. Write ADR: `decisions/NNNN-<slug>.md` (use next available number).
3. Update `README.md` if any public-facing behavior changed.
4. Move `proposals/active/<slug>/` → `proposals/archive/<slug>/`.
5. Propose commit: `"feat: <description> (mewking)"`. Do not auto-commit.

---

## Rules

- Pounce and Stalk: no `status.yaml`, no `proposals/` folder.
- MewKing plan gate is a hard stop — no code before explicit "approve plan".
- `status.yaml` is the source of truth for in-flight state, not conversation memory.
- Never create implementation files during Brainstorm or Spec stages.
- If a feature is already in `proposals/active/`, read its `status.yaml` to resume from the correct stage.
