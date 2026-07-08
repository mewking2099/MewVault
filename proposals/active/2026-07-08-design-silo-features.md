# Design silo — feature roadmap (detailed, implementation-ready)

Status: IMPLEMENTED 2026-07-08 (all 7). Snapshot script requires `npm i -D playwright` per project when first used. Prerequisite work done same day: Impeccable v3 enforcement (post-tool-use guard, design-session trigger, rules update, frontend-design skill disabled).

Build order recommendation: 1 → 3 → 2 → 4 → 5 → 6 → 7. Items 1+3 fit one session.

---

## 1. Audit-score gate on phases — effort S

**What.** Persist every `/impeccable audit` result and block phase progression to `handoff` while P0 findings are open. Same philosophy as the MewKing gate: quality by enforcement, not discipline.

**Implementation.**
- New fields in design-project `Project_Status.md`: `last_audit` (date), `audit_scores` (a11y/perf/theming/responsive/anti-patterns, 0-4), `open_p0` (int).
- Add these fields to the design-silo whitelist in `session-start.js` so they inject each session.
- Capture: extend the `design-session` trigger step 6 — after running the gauntlet, Claude writes scores into Project_Status.md (it already updates that file at wrap).
- Gate: in `pre-tool-use.js`, when an Edit/Write sets `current_phase` to `handoff`/`delivery` on a design project with `open_p0 > 0`, block with exit 2 and the P0 list.
- Dashboard: show audit scores column for design projects (dashboard.py `_load_projects` already parses frontmatter — just add the fields).

## 2. Design token drift detection — effort M

**What.** `mew design tokens --diff` — compare Figma variables against the project's DESIGN.md / token file; flag drift ("Figma changed, code didn't").

**Implementation.**
- New command `mew/commands/design.py` (subcommand `tokens`).
- Read `figma_file_key` from Project_Status.md. Fetch variables via Figma MCP `get_variable_defs` — note: MCP tools are callable by Claude, not the CLI, so implement as a two-step: `mew design tokens --diff` emits the instruction block + parses a saved variables JSON (Claude saves the MCP response to `assets/figma-variables.json` when asked), then diffs against `DESIGN.md` tokens section.
- Output: table of token → Figma value vs code value, mismatches highlighted.
- Doctor: optional `token_drift` check per design project (warn if figma-variables.json older than 14 days).

## 3. Figma comment sync into standup — effort S

**What.** Unresolved Figma comments surface in the morning standup per project.

**Implementation.**
- Extend the `standup` trigger instructions in `session-start.js`: add step — "for each active design project with a `figma_file_key`, fetch unresolved comments via the Figma MCP and list count + oldest age".
- No CLI work needed; it's an instruction change (the Figma MCP does the fetching in-session).
- Format: `brac-uni-usis: 3 unresolved comments (oldest 6d) — <frame links>`.

## 4. Decision provenance, automated — effort S/M

**What.** Design decisions dumped mid-session automatically carry their Figma frame reference and become retrievable.

**Implementation.**
- Extend the `dump` trigger instructions: when silo is design and the dump is classified `decision`, auto-attach `figma_file_key` + ask for the frame link (or pull the currently-discussed frame if one was fetched this session); route to `mewwiki/Operations/Decisions/`.
- Template addition: `templates/` decision note with `figma:` frontmatter field.
- Retrieval already works: doobidoo reindexes on every `mew wiki sync` (built 2026-07-08); decisions resurface via the semantic consult instruction.

## 5. Handoff packager — effort M

**What.** `mew package <project> --design` assembles a client-ready handoff: PRODUCT.md, DESIGN.md, final audit scores, decision log, Figma links, exported assets manifest → one docx/pdf.

**Implementation.**
- Extend `mew/commands/package.py` with a `--design` mode.
- Collect: PRODUCT.md + DESIGN.md (project root), audit fields from Project_Status.md (feature 1), decisions from `mewwiki/Operations/Decisions/` filtered by project tag, `assets/` file manifest.
- Render markdown → docx via pandoc if available, else emit a single handoff.md and let Claude convert in-session.
- Respect existing rule: never push to Drive directly — surface instructions.

## 6. Visual regression snapshots — effort L (needs Playwright)

**What.** On `wrap up` in a design project with a running/buildable site, screenshot key routes to `assets/snapshots/<date>/`, diff against previous set, flag changes next session.

**Implementation.**
- `scripts/snapshot.mjs` (Playwright): reads `snapshot.routes.json` in project root, captures viewport 1440 + 390.
- Pixel diff via `pixelmatch`; write `snapshot-report.md` with changed-route list.
- Wire into `wrap-up` trigger instructions (run if snapshot.routes.json exists) and surface "N routes changed visually" in next session-start via Prior Session section.
- Keep out of hooks (too slow) — trigger-instruction level only.

## 7. Critique-from-screenshot trigger — effort S

**What.** `critique <figma-frame-url | live-url>` — structured design critique from pixels, filed to wiki.

**Implementation.**
- New TRIGGERS entry in `session-start.js`, pattern `/^critique\s+(.+)/i`, arg = target.
- Instructions: fetch screenshot (Figma MCP `get_screenshot` for Figma URLs; Claude-in-Chrome or local screenshot otherwise) → critique against PRODUCT.md audience/voice + heuristics (hierarchy, contrast, density, copy tone, states) → severity-ranked findings → offer to write `wiki/critique-<target>-<date>.md`.
- Works on competitor pages too (fetch-only, no code access needed).

---

## Principles (carry-overs from the July audits)

- No new always-on services. Everything above rides existing hooks, triggers, and CLI.
- Enforcement over advice: anything mandatory becomes a hook gate, not a rules sentence.
- Human-reviewable artifacts land in mewwiki; machine state stays in `.claude/`.
