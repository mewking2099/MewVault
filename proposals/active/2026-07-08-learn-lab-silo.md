# learn-lab silo — specialized skill acquisition (proposal)

Status: BUILT 2026-07-13 (both tracks + srs.py + gates + triggers + dashboard). MewLearn app unblocks after ~2 weeks of usage. Original decision: ONE silo, one track per skill (not silo-per-skill; not inside wiki/ — drill state ≠ notes). First tracks: japanese, trading.

## Why a dedicated silo

Skill acquisition needs state (SRS due-dates, streaks, journal stats) and drills — a different shape from knowledge notes. Shared machinery across tracks: deterministic SRS scheduler, practice triggers, progress in standup/dashboard, concept pages flowing to mewwiki.

## Silo layout

```
learn-lab/
  <track>/
    Track_Status.md        # level/stage, streak, due_count, next_focus (whitelist-injected)
    srs/deck.jsonl         # cards with SM-2 state — only DUE cards ever enter context
    concepts/<slug>.md     # shards, ≤150 lines, flow to mewwiki Knowledge
    sessions/              # practice session logs
```

Scheduler: `scripts/srs.py` (SM-2, deterministic, outside the LLM). Claude grades answers conversationally; the script schedules. Token-aware by construction.

## Track 1: japanese (detailed 2026-07-08)

Method (2026 consensus): kana → kanji early → JLPT-leveled vocab via SRS → structured grammar → immersion.

### Data architecture — the three classes

1. **Learning state — always local.** deck.jsonl, streaks, confusion patterns, studied grammar shards. The irreplaceable asset.
2. **Reference facts — local, from open datasets, never LLM-generated.** JMdict (CC-licensed dictionary), KANJIDIC2 (kanji readings/meanings), community JLPT lists → `reference/` (~few MB JSON, licenses in a manifest). Reason: LLM errors in readings/pitch are uncatchable by a beginner; a wrong flashcard is worse than none. RULE: facts from local canon; Claude verifies against it before any card enters the deck. The SRS script queries reference files — only relevant entries enter context.
3. **Generated practice — LLM on request, ephemeral.** i+1 example sentences (only known words + today's item), conversation drills, why-explanations. Best sentences get promoted into the deck (after verification).

Owned textbooks may sit in raw/ for human reading; Claude does not work through them (token cost, unnecessary given open data + generation). Immersion content stays external — only notes come in.

### Daily workflow (15-30 min)

`practice japanese` → four beats:
1. **Drill** — script emits due cards; quiz both directions (recognition + production); Claude grades; confusion patterns recorded per card.
2. **One new thing** — single grammar point from the JLPT-ordered queue, 3 generated i+1 sentences, saved as shard.
3. **Micro-conversation** — 3-5 exchanges using today's material (the thing no SRS app can do).
4. **Wrap** — script reschedules, streak++, session log, next point queued.

`immersion — <notes>` any time → log + card candidates (JMdict-verified, user confirms). Weekly `japanese review` → progress vs level plan, leech cards, one immersion assignment. Standup: "Japanese: N due · streak N · next: <point>".

### Long-term plan (JLPT-anchored, definitions of done)

| Phase | Target | Done when |
|---|---|---|
| 0 (~3 wks) | Kana automaticity | both kana <2s recall |
| N5 (~mo 1-4) | ~800 vocab, ~100 kanji, core grammar | mock ≥80% + 5-min conversation with Claude |
| N4 (~mo 10) | ~1,500 vocab, ~300 kanji | mock ≥80%; weekly graded-reader immersion habitual |
| N3 (~yr 2) | ~3,700 vocab, ~650 kanji | native content with support |

`Track_Status.md` carries current level; the vault teaches ONLY at level (i+1). Daily consistency > session length — the vault protects the streak, not the volume.

### Mobile decision (resolved direction)

Vault as the brain, **Anki as the phone**: vault curates and exports Anki-importable decks from local reference data; commute reps happen in Anki; desk sessions do tutoring/grammar/conversation/immersion. Optional later: import Anki review stats back.

## Track 2: trading (detailed 2026-07-08)

Research consensus: one concept at a time → 50+ bar-replay setups per concept → 3+ months demo → live small. 6-12 months realistic. The journal + review is the learnable skill; discipline, not prediction.

### Relationship to mew-trade (decided)

mew-trade = the tool (ICT concept library, quant/OHLC analysis, Pine overlays, Phase-2 webhook receiver). learn-lab/trading = the practice (curriculum state, backtest logs, journal, rulebook, reviews, stage gates). **One journal file contract** (`journal/YYYY-MM.jsonl`, schema in the MewLearn PRD) shared by: mew-trade's webhook ingest (auto-writes trade mechanics), the `trade —` trigger (adds psychology fields), and MewLearn's form. mew-trade's backtest page visualizes `backtests/*.jsonl`; its concept library shows per-concept practice status from this track.

### Staged plan with enforced gates

| Stage | Work | Gate (script-computed, vault-enforced) |
|---|---|---|
| 0 Curriculum (~1 mo) | 10 ICT concepts via mew-trade library, beginner→advanced; `teach me` + quiz per concept | quiz passed per concept |
| 1 Backtest (~2-4 mo) | TradingView bar replay, one concept at a time; `backtest — <setup>` logs to backtests/<concept>.jsonl | 50 setups + setup-ID accuracy ≥60% per concept |
| 2 Rulebook v1 | Assembled FROM own backtest stats: setups, kill zones, risk/trade, daily loss limit, max trades/day | user approves; versioned, changes gated |
| 3 Demo (3 mo min) | Full journal (webhook mechanics + manual psychology), daily grade, weekly review, monthly reshape | e.g. 3 consecutive green months + adherence ≥80% + no revenge-pattern flags — encoded in Track_Status, vault refuses live planning until met |
| 4 Live (small) | Same journal, same reviews, unchanged risk rules | ongoing |

### Rhythm

- `market prep` (pre-session): rulebook + today's kill zones + one focus from last review.
- `trade — <details>`: immediate append-only journal entry (mechanics + emotion pre/post + plan + A/B/C adherence grade).
- `trading review`: daily 10-min grade check; weekly win rate / avg R / adherence by setup and hour-of-day + worst behavioral pattern + one focus; monthly strategy reshape + rulebook version bump (gated).

### Notes

- **Budget decision (2026-07-08, $20/mo cap):** TradingView Essential $12.95/mo (annual) from Stage 1 — bar replay included. Webhooks need Plus ($24.95, over budget) → journaling is manual via `trade —` trigger / MewLearn form (~60s/trade; the design already assumed this fallback). Month 1 (curriculum) needs no subscription. Verify on trial: Essential's intraday replay history depth (need ~3 months of M15); if insufficient, FX Replay Intermediate ($17.99/mo) becomes the Stage-1 tool instead — but its built-in journal is NOT used (journal stays in vault files, always). Forex Tester $399 lifetime rejected as premature. mew-trade Phase-2 webhook ingest deferred until/unless TV Plus is ever justified.
- Guardrail (in track rules verbatim): the vault is a discipline coach and pattern analyst — never a signal generator, never financial advice. Most day traders lose money; this system's promise is measured skill development with enforced discipline, not profits.

## Interface strategy (decided 2026-07-08)

Hard constraint: a custom app cannot use the Claude subscription — tutoring/conversation stays in Claude Code. UI covers the LLM-free parts (drills, stats, journaling).

1. **Level 1 — progress page** (build with the silo): generated HTML like `mew dashboard` — streaks, due forecast, JLPT progress, leech cards, trading stats. Read-only, no server.
2. **Level 2 — Anki as the drill UI** (day one): vault exports Anki-importable decks from local JMdict reference data; vocab reps happen on the phone.
3. **Level 3 — MewLearn app** (later, via software silo): local-only web app for desk drills + trading journal. Full PRD: `proposals/active/2026-07-08-mewlearn-app-prd.md`. Build AFTER the tracks have ~2 weeks of real usage data — design from observed patterns, not guesses.

## Build order

1. Silo scaffold + `mew new learning-track <name>` + srs.py
2. Japanese track + practice trigger + Anki export + Level-1 progress page
3. Trading track + trade/review triggers + paper gate
4. Standup/dashboard integration
5. (after ~2 weeks of usage) MewLearn app via the software-silo spec pipeline

## Sources

migaku.com/blog/japanese/learning-japanese-in-2026-what-actually-works · jlptlord.com/blog/best-way-learn-japanese · tradingsim.com/blog/trading-journal-template · plancana.com/blog/trader-segments/day-trading-journal · tradezella.com/blog/your-free-trading-journal-template
