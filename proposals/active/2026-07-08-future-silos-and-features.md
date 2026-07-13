# Future silos + cross-silo features — ALL DESIGNS FINALIZED

Status: B1/B2/B3/B6 BUILT 2026-07-10. Silo designs (A1 career-studio, A2 ops-hub, A3 content-studio) fully finalized 2026-07-10 — build-ready. A3 build stays gated on A1's voice loop. B4 experiment + B5 pending. Say "build <item> from the future proposal".

## FINAL BUILD ORDER

1. **B1** `mew brief` (total-context command — the multiplier)
2. **B2** Instinct v2 (wrap-time reflection)
3. **B6** Android voice capture (small, immediate daily value)
4. **A1** career-studio silo (case studies + confidentiality gate + living CV)
5. **B3** `validate <idea>` (idea-hub)
6. **B4** wireframe→Figma one-screen experiment (timeboxed ~30 min; promote or park on evidence)
7. **A2** ops-hub (next wave — private repo, NO remote, secrets-grade people-data rules)
8. **B5** `ship <project>` — build when the first software project actually reaches shipping
9. **A3** content-studio — DEFERRED until career-studio proves the voice/writing loop

Research context: MewVault already matches the 2026 "AI-first second brain" pattern (execution engine over an Obsidian read layer). The two structural gaps versus current practice: PARA-style **Areas** (long-term responsibilities that aren't projects) and an **output/publish pipeline** (capture and processing are strong; nothing flows out).

---

## A. New silo candidates (ranked)

### A1. career-studio · **BUILT 2026-07-10** (all v1 scope: case studies, CV, skill matrix, mock interviews, gates, triggers)

The near-free one: design projects already carry decisions with Figma provenance, audit scores, and handoff packages.

- `case study <project>` trigger: assemble problem → process → decisions-with-receipts → outcome from existing project data; your voice pass mandatory before it's "done".
- CV maintenance as a living shard; `interview prep <company>` / `talk prep <topic>` from mewwiki People/Meetings/Knowledge.
- Layout: `career-studio/{case-studies/, cv/, talks/, brand/voice.md}`.
- Pros: highest career leverage, reuses all provenance built today. Cons: auto-drafts read hollow without human curation — enforce a "voice pass" checklist before status: done.

**DECISIONS LOCKED (finalized 2026-07-10) — v1 scope: case studies + CV + skill matrix + mock interviews**

- Output target: **portfolio website** (markdown case studies as source; site is a later software-projects build). Silo repo **private, no remote by default**; publishing = export step.
- **Case-study intake, two paths**: (1) **retrospective** — interview-driven for pre-vault projects, artifacts dropped in raw/; these handcrafted studies become the format templates. (2) **auto-assembly** — vault projects assembled from receipts (status history, decisions w/ Figma provenance, audit scores, logs, handoff packages) into the template shape. Build retro mode first. Seed project chosen at build time.
- Pipeline states: `assembled → drafted (after voice pass) → publishable (confidentiality gate only)`.
- **Confidentiality gate (hook-enforced)**: Claude-extracted checklist of every client name/metric/internal detail; owner approves/anonymizes each before `publishable`.
- **Voice profile**: built from **3-5 real writing samples + gap-filling interview**; refined by every voice-pass edit.
- **Living CV**: master + role-targeted shards; `refresh cv` quarterly or on demand; voice pass before external use.
- **Skill matrix** (`skills/matrix.md`): competencies from an **established design-leadership framework adapted at build time**; per skill: level 1-5, evidence links (case studies, projects, learn-lab tracks), last-assessed, target. `skill review` quarterly — Claude challenges unevidenced levels and proposes upgrades from new work. Dashboard tab.
- **Mock interviews** (`mock interview [portfolio|challenge|behavioral|leadership]`): grounded in real vault history (STAR questions from actual projects; portfolio grillings cite real decisions). Sessions logged with scored feedback feeding the matrix. **Cadence: monthly nudge via weekly review + on demand.**

### A2. ops-hub — the Areas silo for the day job · effort M · **DECISIONS LOCKED 2026-07-10**

Home for role work that isn't a project. Private repo, NO remote; people data never flows to shared surfaces.

- **Sensitivity boundary (locked)**: mewwiki People keeps neutral professional profiles (searchable, brief-able); ops-hub holds the sensitive layer — feedback logs, review drafts, 1:1 privates — **excluded from doobidoo indexing**, loaded only inside ops-hub workflows. Rules must state this split; dump routing respects it (a dump classified as sensitive-feedback goes to ops-hub, not mewwiki).
- **1:1 tracker — reports + key stakeholders** (anyone recurring: reports, own manager, key PMs/engineers/clients). Agenda accumulates from dumps between meetings; `1:1 prep <name>` pulls the person's thread (neutral profile from mewwiki + sensitive thread from ops-hub).
- **`feedback log <person>`** — timestamped observations, append-only.
- **Review assembly — self + reports**: quarterly, digests feedback logs + weekly reviews into a self-review draft AND per-report review drafts. Voice pass mandatory; drafts never leave the silo without it.
- **Goals — personal + team**: goals.md with OKRs; standup shows progress; weekly review nudges stalled key results.
- **TWO-EMPLOYER PARTITION (locked 2026-07-10 — owner holds two day jobs, separate MS Teams tenants):**
  - Layout: `ops-hub/{orgs/<org-a>/, orgs/<org-b>/}` — each org gets its own people/, reviews/, goals.md; plus shared `personal-goals.md` (belongs to the owner, not an employer).
  - **The wall**: every ops-hub workflow operates inside exactly ONE org partition per invocation. Person registry (name → org) auto-resolves `1:1 prep <name>` and feedback routing. No artifact mixes orgs unless explicitly requested, and then it's marked cross-org. ops-hub stays out of doobidoo AND out of `mew brief` — neither job can leak via retrieval.
  - **Single merge point**: standup shows both calendars labeled `[org-a]`/`[org-b]` — collision detection between the two jobs' meetings is the daily value.
  - **Connectors**: two M365 MCP instances (one per tenant), both scoped to ops-hub sessions only; workflow partition determines which is queried. Compliance checked per employer; either can fall back to copy-paste independently.

### A3. content-studio — the output pipeline · effort M · **DESIGN LOCKED 2026-07-10, build gated on A1's voice loop**

- **Platforms: LinkedIn + personal blog** (blog = long-form source on the future portfolio site; LinkedIn excerpts from it).
- **Primary source: vault learnings** — weekly reviews, gotchas, concepts ("what I learned building X"). Case-study-derived pieces come later as anchors.
- **Pipeline**: `post about <topic>` → mew brief on the topic → draft against `brand/voice.md` (inherited from career-studio) → critique pass → both platform formats. Confidentiality checklist applies (same gate class as case studies — client names/metrics reviewed before anything is marked ready).
- **Publishing: manual paste, always.** The vault produces final text; no APIs, no auto-posting, ever.
- Publishing calendar as a production/-style backlog; weekly review suggests one post candidate from the week's learnings.

### Third-party integrations across the three silos (locked 2026-07-10)

Principles: MCP connectors are **scoped per silo** (never global — the Webflow lesson); services are **read sources, local files stay the system of record**; writes to external services always require explicit confirmation.

| Service | Silo | Role |
|---|---|---|
| MS Teams (M365 MCP) | ops-hub | standup meetings, 1:1 thread context, meeting capture. Transcripts: Graph access is tenant-controlled — **plan for copy-paste/.vtt fallback into `capture the meeting`**; direct API is a bonus if IT allows. |
| Outlook (M365 MCP) | ops-hub | calendar into standup, flagged-email triage |
| Gmail MCP | ops-hub, career-studio | secondary triage; **`kudos sweep`** — mine praise threads as skill-matrix evidence + self-review material |
| Google Drive MCP | career-studio, exports | import pre-vault artifacts into retro case-study raw/; export packages/reviews only on confirmation |
| Discord | — | out of v1 entirely; revisit only if a team actually lives there |
| Gemini subscription | auxiliary | NOT in the Claude Code path (subscription can't be a model source; no proxies ever). Uses: Gemini CLI (Google-account auth) as a `mew dispatch` engine experiment for bulk/long-context tasks; NotebookLM as a learn-lab export target (audio overviews of grammar/ICT shards). |

Compliance note: connecting work Teams/Outlook to a personal vault touches employer data policy — verify what's permitted before wiring, even read-only. Sensitive ops-hub content remains excluded from semantic indexing regardless of source.

### Rejected for now
Finance/life-admin silo — dilutes focus; the vault's strength is professional context.

---

## B. Features inside existing silos (ranked)

### B1. `mew brief <topic>` — the total-context command · effort M · BUILD FIRST · **DECISIONS LOCKED 2026-07-08**

Cross-silo context pack: doobidoo hits + mewwiki decisions + log.md mentions + specs + mechanic shards, deduped, ranked (decisions/specs > raw log lines), every line source-cited. Structure: Facts / Decisions (dated) / Open threads / Related files.

Locked decisions:
- **People/Meeting notes: included by default** (briefs on clients pull who-said-what).
- **Output: injected pack + saved artifact** → `mewwiki/Knowledge/briefs/<topic>-<date>.md`.
- **Budget: 2,000 tokens hard cap**, drop-by-priority (session-start pattern).
- **Auto-wired**: `meeting prep`, `spec`, and `design session` triggers run a brief first — total context is the default.

### B2. Instinct v2 — learn from corrections · effort S/M · **BUILT 2026-07-10**

Locked design: **wrap-time reflection** (no transcript regex, no new hooks). The wrap-up trigger gains a step: Claude reviews the session in-context for corrections and proposes 0-3 instinct candidates (assumption → what the user actually wanted → reusable rule), each with a **proposed scope** (project / silo / global) the user can adjust. On live confirmation → written **straight to instincts/promoted/** (active next session; `mew instinct prune` is the undo). Unwrapped sessions learn nothing — acceptable trade for zero noise.

### B3. idea-hub: `validate <idea>` · effort S/M · **DECISIONS LOCKED**

Market scan → competitor table (who/positioning/pricing/gap), market-size signal, tech complexity, effort estimate (S/M/L/XL) → `feasibility.md` with inline citations → ends with pursue/park/kill recommendation.
- **Depth: quick scan default** (~10 min, kills weak ideas cheaply); `--deep` flag for fan-out research on survivors.
- **Status stays owner-controlled**: the workflow presents evidence; only the user flips `status: validated`.

### B4. design: `wireframe <spec>` — spec → Figma · effort M/L (experimental)

Figma MCP write direction (`generate_design`): push low-fi frames into Figma from a written spec/PRD. Prototype on one screen first; quality unproven — timebox the experiment.

### B5. software: `ship <project>` · effort S/M

Version bump + changelog generated from log.md entries since last tag + GitHub release + deploy checklist (Vercel). Closes the loop CI opened.

### B6. capture: mobile voice → inbox · effort S · **BUILT 2026-07-10**

Android → drop-folder pattern: voice note/dictation in any note app that exports text to a synced folder (Syncthing or Google Drive folder → symlinked/synced into `mewwiki/_inbox/`), or Tasker for one-tap capture. Design around a generic watched drop-folder so any device works. Inbox discipline unchanged: nothing auto-processes; "process the inbox" routes items.

---

## Suggested order

B1 → B2 (multipliers for everything existing) → A1 career-studio (first new silo) → B3 → B6 → then reassess A2/A3/B4/B5.

## Principles (unchanged)

No new always-on services · enforcement over advice · human artifacts in mewwiki, machine state in `.claude/` · token budgets are structural (indexes + shards, never whole-tree reads).

## Sources

buildingasecondbrain.com/ai-second-brain · mindstudio.ai/blog/build-ai-second-brain-claude-code-obsidian · taskade.com/blog/ai-second-brain-tools · storyflow.so/blog/what-is-ai-second-brain-complete-guide
