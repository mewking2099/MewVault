# Plan: always-on-memory (doobidoo + graphify, all silos, automatic)

## Tier: MewKing
## Status: PENDING APPROVAL

## Summary

Make both semantic memory (doobidoo → ChromaDB + Ollama) and code knowledge graph (graphify) run automatically across every mewvault silo. Today, graphify only runs on mewvault, doobidoo is wiki-scoped and stale since 2026-07-24, and both require manual invocation. This plan (a) extends graphify to run in every silo on a `graphify update .` post-session tick, (b) replaces the MCP-only doobidoo harvest path with a direct-to-ChromaDB Python indexer that shell hooks CAN call, (c) unifies the ChromaDB store into a single collection with a `silo` metadata field, (d) instructs Claude via CLAUDE.md and session-start injection to query both systems before any file reads. Net effect: after any session that touched files, the correct silo's graph and vector index update without human intervention; on the next session-start, Claude is told about both and reminded to query them first.

## Uncertainties (call out explicitly)

- **U1 — ChromaDB HTTP mode vs embedded.** `session-start.js` currently checks `localhost:8000` (HTTP mode) and `localhost:8001` (v2 heartbeat); the doobidoo MCP config points at a SQLite path (`~/.mewvault/chroma-wiki/memory.db`), i.e. embedded mode. The two paths cannot both be authoritative — plan assumes we standardize on the embedded PersistentClient (SQLite-backed) and drop HTTP references. Confirm before implementation.
- **U2 — Ollama availability outside sessions.** doobidoo uses Ollama at `localhost:11434` for embeddings. If Ollama is not running when the hook fires, the direct-index script must either (a) fall back to `sentence-transformers` locally or (b) queue and defer. Plan proposes (b) — a `pending-index-queue.jsonl` drained on next session-start. Confirm which fallback is acceptable.
- **U3 — Career-studio privacy.** career-rules.md says career content stays OUT of shared surfaces. Plan proposes indexing it into a **separate ChromaDB collection** (`mewvault-career`) that is NEVER included in cross-silo queries. Confirm this treatment.
- **U4 — Chunking strategy.** Currently unspecified. Plan proposes: for `.md`, chunk by heading with 512-token overlap-0 chunks; for code (`.ts`, `.py`, `.gd`), chunk by top-level symbol (function/class), max 512 tokens, spillover truncated with a `truncated: true` flag.
- **U5 — Graphify + Impeccable co-existence.** Frontend prototype files (`index.html`, `app.js`, `styles.css`) can be huge. Graphify handles these but doubles up on Impeccable's ban scanner. No conflict expected but flag if we see graph noise from generated CSS.

## Phases

### Phase 1: unified ChromaDB indexer (no MCP required)

- Add `mewvault/scripts/index_silo.py` — a standalone Python script using ChromaDB's `PersistentClient` API directly (bypassing the MCP stdio limitation).
- Interface:
  - `python3 mewvault/scripts/index_silo.py --silo <silo> [--files <path,path,...>] [--full]`
  - `--files` = incremental (index only these paths); no flag = incremental since last run (mtime > `.last-index-run`); `--full` = wipe and reindex.
- Uses the same embedding provider doobidoo uses (Ollama `nomic-embed-text`). Falls back to queue-on-disk if Ollama unreachable (see U2).
- One ChromaDB PersistentClient at `~/.mewvault/chroma/`, three collections:
  - `mewvault-shared` — mewwiki + design-studio + software-projects + game-lab + idea-hub + mewvault (queryable cross-silo), each doc has `silo` metadata
  - `mewvault-career` — career-studio only, isolated (see U3)
  - `mewvault-learn` — learn-lab only, low prose (see Risks)
- Doc ID format: `<silo>::<relpath>::<chunk_index>`, so incremental re-index of one file deletes prior chunks by ID prefix and upserts fresh.
- Metadata schema: `{ silo, path, ext, chunk_index, chunk_type: "heading"|"symbol", heading?, symbol?, mtime, ingested_at }`.

### Phase 2: graphify runner script

- Add `mewvault/scripts/graphify_silo.py` — thin wrapper that runs `graphify update .` in a given silo directory. If the silo has no `graphify-out/` yet, runs `graphify build .` on first invocation instead.
- Silo → path map:
  - `mewvault` → `mewvault/`
  - `code` → `software-projects/<project>/` (per-project, not silo-wide)
  - `game` → `game-lab/<project>/` (per-project)
  - `design` → `design-studio/<project>/` (per-project)
  - `wiki` → `mewwiki/` (single graph for the whole wiki)
  - `idea` → `idea-hub/` (single graph)
  - `career` → `career-studio/` (per U3 confirm — likely SKIP; low value + private)
  - `learn` → SKIP (structured SRS data, low prose value)
- Because graphify is AST-only + no API cost, this is safe to run in a hook.
- Timeout guard: 30s hard cap; if `graphify update .` exceeds, write to `~/.mewvault-hook-errors.log` and move on. Session end must never block.

### Phase 3: session-end hook wiring

- Modify `mewvault/hooks/session-end.js` to, after the existing wiki-sync block:
  1. Detect the silo + active project (already partially done — extend `detectSilo` to return `career`, `idea`, `learn` too).
  2. Spawn `python3 mewvault/scripts/graphify_silo.py --silo <silo> --project <dir>` **detached**, `stdio: 'ignore'`, `unref()` — hook returns immediately.
  3. Spawn `python3 mewvault/scripts/index_silo.py --silo <silo> --files <files_modified>` **detached** the same way.
  4. Write `.claude/pending-vector-index.json` regardless (already exists) — the file becomes a session-start signal, not the trigger. It records what was queued.
- Remove the current `indexToChromaDb` HTTP block (dead code — MCP config uses embedded mode, no HTTP server on :8000).
- Nothing blocks. Hooks stay under 100ms wall clock.

### Phase 4: session-start hook wiring

- Modify `mewvault/hooks/session-start.js`:
  1. Extend `AGENT_MAP` to include `career`, `learn`, `idea` silos (currently missing — falls back to mew-chief).
  2. Extend `detectSilo` and `WHITELIST` (already have `career`, `idea` — add `learn`).
  3. Rewrite `loadSemanticContext(silo, workspaceRoot)`:
     - Drop the HTTP `queryChromaDb` port 8000 branch (dead).
     - Drop the `mcps.doobidoo` gate — always emit the semantic-recall instruction if `~/.mewvault/chroma/` exists (i.e. the store is initialized), independent of MCP status.
     - Text: mandatory instruction telling Claude to call `mcp__doobidoo__retrieve_memory` (if MCP available) OR to run `python3 mewvault/scripts/query_index.py --silo <silo> --q "<keywords>"` (fallback) before any substantive work.
  4. Add a new section (7c) `## Graphify` that injects the correct graphify-out path for the current silo/project. If `<project>/graphify-out/graph.json` exists, tell Claude: "Query `graphify query \"<task>\" --root <project>` before reading files."
- Extend `checkServices` to poll the ChromaDB PersistentClient store (file existence + last-mtime health, not HTTP) and Ollama (`localhost:11434/api/tags`, 500ms timeout). Report as `ChromaDB (store)` and `Ollama` in the services block.

### Phase 5: CLAUDE.md standing rule

- Add a new section to `/Users/Mohabbat/Jan/mewvault/CLAUDE.md` titled **## Context retrieval — mandatory before file reads**, with these bullets:
  - Before any substantive read (spec, plan, code, wiki), first query semantic memory: call `mcp__doobidoo__retrieve_memory` with 2–3 keywords from the task (fallback: `python3 mewvault/scripts/query_index.py --silo <silo> --q "<keywords>"`).
  - If the current project or silo has `graphify-out/graph.json`, also run `graphify query "<task>"` for structural context.
  - Cite anything used as `(source: mewwiki/<slug>)` or `(source: graph:<node>)`.
  - Skip only when the task is a pure command (e.g. `mew doctor`) with no context need.
- Also add a **## Automatic indexing** section stating that graphify + semantic indexing run automatically at session-end; no manual invocation is required or expected.

### Phase 6: query helper for the fallback path

- Add `mewvault/scripts/query_index.py` — CLI for querying the unified ChromaDB store when MCP is not connected.
- Interface: `python3 mewvault/scripts/query_index.py --silo <silo|any> --q "<query>" [--n 5] [--collection <name>]`.
- Prints ranked results as `<path> :: <heading|symbol> — <snippet 200 chars>` with `(silo: X)` tag.
- Used by hooks and by Claude when the MCP is offline.

### Phase 7: migration — one-time full reindex

- Add `mewvault/scripts/reindex_all.py` — iterates every silo + project, runs full graphify build and full semantic reindex.
- Ordered:
  1. Wipe `~/.mewvault/chroma/` (or archive to `~/.mewvault/chroma-backup-<date>/`).
  2. For each silo in `[wiki, design, code, game, idea, mewvault]` (skip `learn`, `career` unless per U3):
     - Run `graphify build .` per project or per silo root.
     - Run `index_silo.py --silo <silo> --full`.
  3. Report counts (files indexed, chunks, graph nodes) per silo.
- Owner runs this once after approval. Estimated time: 5–15 min depending on Ollama throughput.

### Phase 8: doobidoo MCP config alignment

- Update `mewvault/mcp-configs/doobidoo.json`:
  - Point `MCP_MEMORY_SQLITE_PATH` at `~/.mewvault/chroma/memory.db` (the new unified store).
  - Change `silo_scope` from `["wiki"]` to `["wiki", "design", "code", "game", "idea", "mewvault"]`.
- Update `mewvault/mcp-configs/chromadb.json` (referenced in `session-start.js` line 443) — either delete (if it's the dead HTTP config) or rewrite to point at the unified store. Confirm which before editing.

## Files

### Created
- `mewvault/scripts/index_silo.py` — direct ChromaDB indexer, silo-aware, MCP-free
- `mewvault/scripts/query_index.py` — CLI fallback query for the unified store
- `mewvault/scripts/graphify_silo.py` — thin wrapper around `graphify update .` with silo→path mapping and timeout guard
- `mewvault/scripts/reindex_all.py` — one-time migration runner
- `mewvault/proposals/active/always-on-memory/plan.md` — this file
- `mewvault/proposals/active/always-on-memory/status.yaml` — `status: pending_approval`

### Modified
- `mewvault/hooks/session-end.js` — spawn graphify + index scripts detached after wiki sync; remove dead HTTP indexer; extend `detectSilo` to cover all silos
- `mewvault/hooks/session-start.js` — rewrite `loadSemanticContext` (drop dead HTTP path, unconditional instruction); add graphify section 7c; extend `AGENT_MAP` + `WHITELIST` for missing silos; add ChromaDB store + Ollama to `checkServices`
- `mewvault/CLAUDE.md` — add "Context retrieval — mandatory before file reads" and "Automatic indexing" sections
- `mewvault/mcp-configs/doobidoo.json` — point at unified store, widen `silo_scope`
- `mewvault/mcp-configs/chromadb.json` — align or delete (pending U1)

### Deleted
- (none in this plan — `pending-vector-index.json` staging file stays but becomes informational only)

## Risks

- **R1 — Ollama slow / offline.** If embeddings block session-end, sessions feel sluggish. **Mitigation:** spawn detached + `unref()`; queue-on-disk fallback if Ollama unreachable; drain queue on next session-start (background).
- **R2 — ChromaDB corruption.** A crash mid-write can corrupt the SQLite store. **Mitigation:** `reindex_all.py` archives the prior store to a timestamped backup before wiping; `mew doctor` grows a "chroma store health" check.
- **R3 — Silo bleed.** career-studio content leaking into cross-silo results violates the privacy rule. **Mitigation:** separate collection (`mewvault-career`), never queried by default; `query_index.py` refuses `--silo any` for the career collection; unit test asserts isolation.
- **R4 — Cache invalidation.** session-start.js is cache-optimized (comment at line 1222). Changing the section order breaks Anthropic prompt caching and burns tokens. **Mitigation:** add new sections at the *end* of the static block (before dynamic content) and keep existing section order untouched. Verify cache hit ratio via `mew usage --report` after rollout.
- **R5 — Claude ignores the instruction.** The system-prompt rule "query first" is soft (no hook enforcement). **Mitigation:** add a PreToolUse hook (later, out of scope for this plan) that warns on the first `Read` call of a session if `mcp__doobidoo__retrieve_memory` hasn't been called. Track via session state file. Note in plan as follow-up work.
- **R6 — Graph noise from generated files.** `graphify-out/` inside a project could recursively pick up its own artifacts on the next `graphify update`. **Mitigation:** ensure `.graphifyignore` (or graphify's default ignore) excludes `graphify-out/`, `node_modules/`, `dist/`, `.next/`, `.svelte-kit/`, `.godot/`, `export/`. Verify by inspecting one silo's graph.json after first run.
- **R7 — Hook timeout on large silos.** software-projects/dsaas is 5.7GB, first-time index could exceed session-end budget. **Mitigation:** first-time full index runs via `reindex_all.py` (manual, once); ongoing hook runs are incremental only (files touched this session), always small.
- **R8 — Learn-lab low value.** Structured SRS data (JSONL decks) is not prose; semantic embeddings are ~useless. **Mitigation:** skip `learn` silo entirely (both graphify and semantic). Confirmed as `SKIP` in Phase 2 map.

## Success criteria

- [ ] `python3 mewvault/scripts/reindex_all.py` completes without error and reports counts for every non-skipped silo
- [ ] `~/.mewvault/chroma/` exists and contains at minimum `mewvault-shared` collection with ≥100 documents from a mix of ≥3 silos (verify via `query_index.py --silo any --q "test"`)
- [ ] `graphify-out/graph.json` exists in mewvault, mewwiki, idea-hub, and at least one project each in software-projects, design-studio, game-lab
- [ ] After a session that modifies 1+ file: `session-end.js` fires; within 30s the modified file's chunk in ChromaDB has a fresh `ingested_at` timestamp, and the relevant silo's `graphify-out/graph.json` mtime is updated
- [ ] Next session-start after that shows the semantic-recall + graphify sections in the injected system prompt (verify via `MEW_SESSION_START_DEBUG=1 node hooks/session-start.js < test-input.json`)
- [ ] Cache hit ratio (`mew usage --report`) does not drop >5pp compared to pre-rollout baseline (guards against R4)
- [ ] `mcp__doobidoo__retrieve_memory` returns fresh results (< 24h) for a query about a file modified in the last session (end-to-end proof)
- [ ] career-studio content is NOT returned by `query_index.py --silo any --q "<career keyword>"` (isolation test)

## Rollback

Reversible in three steps:

1. `git revert` the commits touching `hooks/session-end.js`, `hooks/session-start.js`, `CLAUDE.md`, and the mcp-configs. Hooks return to prior behavior immediately.
2. `mv ~/.mewvault/chroma ~/.mewvault/chroma-abandoned-<date>` — the unified store is contained in one directory; removing it is safe (no other consumers).
3. `rm -rf <silo>/graphify-out/` per silo if we want to reclaim disk. Graphify outputs are regenerable at any time via `graphify build .`; deleting them costs nothing except the next build's wall time.

The two new scripts (`index_silo.py`, `query_index.py`, `graphify_silo.py`, `reindex_all.py`) can stay on disk — unused code is harmless. Or delete them with the revert commit if a clean tree is preferred.

## Post-approval next steps

1. Owner writes `approved` in this thread.
2. Update `status.yaml` → `status: approved`.
3. Implementation order: Phase 1 → Phase 6 → Phase 2 → Phase 7 (one-time migration, run and verify) → Phase 3 → Phase 4 → Phase 5 → Phase 8.
4. Verify success criteria after each phase; stop and report on any failure.
