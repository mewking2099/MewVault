# PRD — MewLearn (learn-lab interface app)

status: draft            <!-- draft → approved → implemented -->
target-silo: software-projects/mewlearn
stack: next (Next.js + TS + Tailwind, per silo convention)
tier: stalk
created: 2026-07-08
prerequisite: learn-lab silo built + ~2 weeks of real track usage
flow: when scaffolding the project, copy this file into `raw/` as the brief; distill Phase specs from it via the `spec <feature>` pipeline.

## Problem

Learning inside a terminal works for tutoring (chat is chat) but is hostile to drills and data entry: flashcard reps need speed and tactility; trade journaling needs a form you can complete in under two minutes right after a trade, or it won't happen. Both tracks live or die on daily friction.

## One-liner

A local-only web app over the `learn-lab/` files: flashcard drills, trading journal, and progress views. No cloud, no auth, no LLM calls (tutoring stays in Claude Code — subscription constraint).

## Users & context

One user: the vault owner. Desktop primary; must be usable from a phone browser on the same LAN (laptop IP:port) for couch drills. Product lane (Impeccable): app UI — density, semantic states, speed over decoration.

## Architecture constraints (non-negotiable)

- **Local only.** `npm run dev`-style local server (Next.js API routes reading/writing `~/Jan/learn-lab/` via `MEWVAULT_WORKSPACE` env). Never deployed. No network calls except LAN serving.
- **Files are the API.** The app reads/writes the SAME files the vault uses: `deck.jsonl`, `journal/*.jsonl`, `Track_Status.md` frontmatter. No database. If the app dies, nothing is lost; Claude Code sessions and the app stay in sync by construction.
- **One scheduler implementation.** SM-2 lives in ONE TypeScript lib inside this app, exposed as a small node CLI (`npx mewlearn-srs due|grade`) that the vault's `practice japanese` trigger ALSO calls. Never two implementations (drift = corrupted scheduling).
- **Writes are append/atomic.** deck grading appends a review event then rewrites the card line atomically; journal entries are append-only (immutability rule). File lock or write-queue to survive the vault editing concurrently.
- **No LLM in-app.** Buttons may deep-link a suggested Claude Code prompt (copy to clipboard), nothing more.

## Data contracts (source of truth — vault and app both honor these)

Card (deck.jsonl, one JSON per line):
```json
{"id":"n5-0042","front":"食べる","reading":"たべる","back":"to eat","level":"N5","tags":["verb","ichidan"],
 "srs":{"ease":2.5,"interval":4,"due":"2026-07-12","reps":6,"lapses":1},"confusions":["飲む"],"source":"jmdict:1358280"}
```

Trade (journal/YYYY-MM.jsonl, append-only):
```json
{"ts":"2026-07-08T14:32:00","instrument":"NQ","direction":"long","entry":18250.5,"exit":18262.0,"size":1,
 "r_multiple":1.4,"setup":"ict-fvg","emotion_pre":"calm","emotion_post":"satisfied","plan":"waited for FVG retest",
 "followed_rules":true,"grade":"A","stage":"paper","notes":""}
```

## Phase 1 — Japanese drills (MVP)

Screens: Session (card front → reveal → grade), Session summary, Deck overview.

- **AC-1** Given cards are due, when I open the app, then I see the due count and can start a session showing one card at a time (front only, reading hidden).
- **AC-2** Given a revealed card, when I press Again/Hard/Good/Easy (keyboard 1-4), then SM-2 reschedules it, the write hits deck.jsonl atomically, and the next card appears in <200ms.
- **AC-3** Given I grade a card Again, then it re-enters the current session queue (lapse recorded).
- **AC-4** Given a session ends (queue empty or I quit), then I see reps done, accuracy, streak status, and time spent; Track_Status.md streak/due fields update.
- **AC-5** Given the vault modified deck.jsonl since app load, when I grade, then the write does not clobber vault changes (reload-merge or per-line rewrite).
- **AC-6** Given my phone is on the same LAN, when I open laptop-ip:port, then the session screen is fully usable (thumb-sized grade buttons, no horizontal scroll at 390px).

## Phase 2 — Trading journal

Screens: New trade (the 2-minute form), Journal list (month), Stats.

- **AC-7** Given a closed trade, when I fill the form (instrument, direction, entry/exit, size, setup tag, emotion pre/post, plan, followed_rules, grade), then it appends to the month's journal file in <2 min end-to-end; required fields block submit.
- **AC-8** Given existing entries, journal list shows them newest-first with day grouping; entries are read-only after save (immutability), with an "append correction note" affordance only.
- **AC-9** Stats view computes from files on load: win rate, avg R, adherence rate (grade A%), breakdown by setup tag and by hour-of-day; paper/live shown separately; `stage: paper` banner always visible while paper.
- **AC-10** Given rulebook.md, the New-trade form shows the current rule checklist inline (read-only) before the submit button.

## Phase 3 — progress & polish

- **AC-11** Progress screen: JLPT level progress (cards learned/target), 30-day due forecast chart, streak calendar, leech list (lapses ≥4).
- **AC-12** Anki export button: writes an .apkg-compatible (or TSV) export of selected levels to learn-lab/japanese/exports/.
- **AC-13** Kana practice mode: timed kana → romaji rounds, results feed Phase-0 "automaticity" metric (<2s avg).

## Edge cases

Empty deck / no due cards (celebrate, show forecast — never a dead end); malformed jsonl line (skip + surface count, never crash); timezone day-boundary for streaks (local midnight, one config); huge deck (10k cards — due computation stays <100ms, index by due date); two app tabs open (last-write-wins per card line with review-event append preserving history); workspace path missing (setup screen pointing at env var).

## Out of scope

Cloud sync/accounts/deploy · in-app LLM chat or API-key features · charting/market data in the journal (numbers come from the user; analysis of markets is not this app) · gamification beyond streaks · multi-user.

## Success metrics

Japanese: daily streak survives ≥21 consecutive days within the first month of app use (vs terminal-only baseline). Trading: median journal-entry time <2 minutes; 100% of trades journaled in paper stage (count vs user's own report).

## Design notes (for the Impeccable pass)

Product lane. Session screen is 90% of usage — design it first, everything else is furniture. Grade buttons: fixed thumb zone on mobile, 1-4 keys on desk. Dark-mode default (evening practice). The pre-ship gauntlet (audit/clarify/harden) applies; harden especially: long Japanese strings, huge decks, offline LAN quirks.
