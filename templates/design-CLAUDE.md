# Silo: design-studio — UX/UI Work

Flat layout. Project status lives in frontmatter, not folder names.

## Phase structure (per project)

| # | Phase | Output |
|---|---|---|
| 0 | Discovery | `00_discovery/brief.md`, `stakeholders.md`, `constraints.md` |
| 1 | Analysis | `01_analysis/personas.md`, `jtbd.md`, `competitive.md` |
| 2 | Synthesis | `02_synthesis/insights.md`, `opportunity-map.md` |
| 3 | UX Audit | `03_audit/heuristics.md`, `findings.md` (redesigns only) |
| 4 | UI Prototyping | `04_ui/wireframes/`, `design-decisions.md`, `figma-snapshot.md` |
| 5 | Handoff | `05_handoff/specs.md`, `asset-export.md`, `dev-notes.md` |

## Project_Status.md schema

```yaml
project: <name>
client: <client>
started: YYYY-MM-DD
status: active | greenlit | blocked | archived | abandoned
confidential: false
current_phase: 0
phase_status: in_progress | blocked | review | done
last_session: YYYY-MM-DDTHH:MM
last_wrap: YYYY-MM-DDTHH:MM
next_action: ""
open_questions: []
figma_file_key: null
greenlit: false
promoted_to: []
```

## Rules

- Phase transition only via "advance the phase" trigger — not manual edits.
- "sync figma" at phase 4 start — requires `figma_file_key` set in status.
- Figma tokens are per-project: `mew secret set FIGMA_TOKEN --scope <project>`.
- Client deliverable package excludes: personas, JTBD, opportunity maps, draft notes.
