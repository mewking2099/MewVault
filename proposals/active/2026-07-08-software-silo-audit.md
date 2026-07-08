# Software silo audit — findings + path to spec-driven development

Audited 2026-07-08. Context: the owner is a product design lead with little coding knowledge. Quality therefore cannot come from reading code — it must come from automated verification and spec traceability. That principle drives every recommendation below.

## Findings

**F1 — Zero tests across all 7 projects. Zero CI.** Not one `.test.*` or `.spec.*` file anywhere; no `.github/workflows` in any project. The TDD gate in `pre-tool-use.js` exists but is warning-only, and warnings get ignored. `yaana-design-system` even has a `test` script with nothing to run. This is the single biggest risk: nothing verifies that anything works except manual clicking.

**F2 — Lint/typecheck scripts exist but nothing runs them.** Most projects have `lint`/`typecheck` in package.json — good — but with no CI and no gate, they run only when someone remembers.

**F3 — WIP sprawl.** 7 projects marked `active`; last_session dates show neustring-copilot idle since 05-12, golddiamondclub since 05-21, mewvault-site since 06-02, yaana-design-system since 06-04. Four of seven are stale but still "active". Divided attention produces half-finished products.

**F4 — Specs exist but have no downstream life.** `raw/` is well used (dsaas: 21 files, mewvault-site: 23). But nothing connects a spec to acceptance criteria, criteria to tests, or tests to "done". A spec that doesn't gate anything is documentation, not specification.

**F5 — What's working.** Tier gates are respected (`plan_approved: true` on all three MewKing projects — the hard gate works, proving enforcement beats advice). Stacks are consistent (mostly Next.js + TS). `raw/` immutability and status hygiene are decent. Two projects lack tsconfig (mew-trade, neustring-copilot are non-TS or mixed — acceptable given their stacks).

## Recommendations

### R1 — Spec-driven development flow (the core change)

Every feature goes through this pipeline. You review at the two starred points — both are product language, not code:

```
raw/<feature>-brief.md          (you write or dump — the intent)
      ↓  Claude distills
specs/<feature>.md              ★ you review: numbered acceptance criteria,
                                  Given/When/Then, out-of-scope list
      ↓  MewKing/Stalk plan approval (existing gate)
tests/ written FROM the criteria, before implementation
      ↓
implementation until tests pass
      ↓
wrap references criteria IDs    ★ you review: "AC-1 ✓ AC-2 ✓ AC-3 deferred"
```

Implementation in MewVault:
- `templates/spec.md.tmpl` — problem, user story, numbered acceptance criteria (AC-1…), edge cases, out-of-scope, success metric.
- New trigger `spec <feature>` in session-start.js: distill the raw brief into specs/<feature>.md, stop for approval, refuse implementation until approved (Project_Status field `spec_approved`).
- Upgrade the TDD gate from warn to **block** for stalk/mewking projects: creating `src/**` files with no matching test fails with exit 2 and instructions to write the test from the acceptance criteria first. Pounce stays warn-only.
- Wrap ties results to criteria IDs in log.md.

### R2 — CI as the non-coder's safety net

You can't review a diff, but you can read a green check. One GitHub Actions workflow per project running `typecheck → lint → test → build` on every push. Red = not done, regardless of what the session log claims.

- `templates/ci.yml.tmpl`; `mew new code-project` writes it automatically; a one-time `mew ci install` backfills existing projects.
- Doctor check: active code project without CI file → warn.

### R3 — Definition of Done, enforced at wrap

"Done" currently means "Claude says so". Change wrap for code projects: before writing the log entry, run `npm run typecheck && npm run lint && npm run build` (and `test` when R1 lands) and paste the pass/fail into the log. A failed check downgrades the log entry to `[incomplete]` and sets next_action to the failure. This makes every log entry a verified claim.

### R4 — See the product, not the code: preview deploys

Connect the Next.js projects to Vercel (free tier). Every push gets a preview URL. You review the actual product in the browser — the exact skill you're strongest at — instead of trusting descriptions. Pairs with the Impeccable pre-ship gauntlet on the frontend.

### R5 — WIP limit

Pick the 2-3 projects that matter now; `mew archive` or mark `status: paused` for the rest. Add a doctor check: more than 3 projects `active`, or any active project idle 21+ days → warn. Fewer, finished products beat seven half-built ones — this is a product-management truth, not a coding one.

### R6 — Dependency and secret hygiene

`npm audit --audit-level=high` as a CI step; lockfiles always committed; the existing secrets guardian already covers keys. When a project ships to real users, add Renovate for automated dependency PRs (CI green = safe to merge — again, readable without code knowledge).

### R7 — Scalability defaults in templates (so you never think about them)

Baked into `mew new` scaffolds, not remembered per project: env-var validation at startup (fail loud, not silently misconfigured), error boundaries + a 500 page, database access only through a single client module (swap/scale later without hunting), and migrations-as-files from day one for any project with a database (Supabase projects especially).

## Suggested order

R5 today (it's a decision, not code) → R1 + R3 next session (the pipeline) → R2 (CI templates) → R4 (Vercel, per project as each nears shipping) → R6/R7 (roll into templates once).

The through-line: you already proved enforcement works — plan_approved is respected on every MewKing project while the advisory TDD warning achieved nothing. Move quality checks from advice to gates, and put your review points where your expertise is: specs and the running product.
