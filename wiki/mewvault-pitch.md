# MewVault — the AI workspace that enforces its own quality bar

*A federated personal workspace built on Claude Code. You talk to it in plain English; it runs your projects, guards your quality standards, remembers every decision, and pushes you to keep growing. Everything lives in plain files you own.*

**Who it's for:** designers, product people, and builders who work with an AI assistant daily and are tired of three things — re-explaining context every session, AI work that claims "done" without proof, and knowledge that evaporates when the chat ends.

---

## New in this release

### learn-lab — a personal skill academy with real discipline

Structured skill acquisition, not chatbot tutoring. Ships with two tracks and a shared engine:

- **Deterministic spaced repetition.** A local SM-2 scheduler decides when flashcards return — the AI grades your answers conversationally, but never touches the scheduling math. Only due cards enter the session (token-efficient by construction). One-command Anki export for phone practice.
- **Language track (Japanese).** Daily 20-minute sessions: drill → one new grammar point with example sentences at exactly your level → a short conversation using only words you know. Facts come from locally downloaded open dictionaries (JMdict/KANJIDIC2), never from AI memory — a wrong flashcard is worse than none, so every card is verified before it enters the deck. Comes pre-seeded with a full kana deck; practice works on day one.
- **Trading track (discipline-first).** Stage-gated progression: curriculum → backtesting (50 logged setups per concept, accuracy threshold) → personal rulebook written from your own stats → months of demo trading → live. The vault *refuses* to help with activities beyond your current stage. The journal is append-only at the system level — history can't be rewritten. Reviews grade rule-adherence, never profit. Explicitly not a signal generator and not financial advice: the promise is measured skill development with enforced discipline.

### career-studio — your career, compounding automatically

A private silo (own repo, never pushed anywhere) that turns daily work into career assets:

- **Case studies that write themselves from receipts.** Projects done inside the vault carry their decision history, quality scores, and artifacts — case studies assemble from that record. Older projects get an interview-driven retrospective mode.
- **A confidentiality gate you can't forget.** Nothing becomes publishable until you've approved a checklist of every client name, metric, and internal detail — enforced by the system, not by memory.
- **A voice profile** built from your real writing, so drafts sound like you and improve with every edit you make.
- **A living CV** refreshed quarterly from actual vault activity.
- **Mock interviews grounded in your real history** — behavioral questions cite your actual projects and decisions, not a question bank. Scored, logged, monthly cadence.

### The skill compass — growth you can see, and can't quietly abandon

Built for the multi-disciplinary era: instead of one profession ladder, a five-pillar matrix (your anchor craft + the disciplines you're growing into). Every claimed level requires linked evidence; trend per skill is computed from evidence recency. The dashboard shows it visually — level dots, growth arrows, dormant pillars highlighted. The weekly review names your most neglected pillar and proposes exactly one activity to feed it. The health monitor warns when nothing new has been learned in 30 days. The system doesn't just track growth — it nags.

### Cross-silo intelligence

- **`brief <topic>`** — the total-context command: everything the vault knows about a topic (decisions, meeting notes, specs, logs) in one ranked, source-cited page. Auto-runs before meeting prep and spec work.
- **Instinct learning v2** — at session wrap, the AI reflects on where you corrected it and proposes reusable rules; confirmed ones permanently change its behavior. The assistant in month six makes fewer of month one's mistakes.
- **`validate <idea>`** — market scan with cited competitor tables and a pursue/park/kill recommendation before anything gets built.
- **Mobile capture** — a voice note on your phone lands in the vault inbox via a synced folder. Ideas stop dying between desk sessions.

### Game development, learning-first (Unity + Godot)

The AI writes all the code and explains it; you do every editor step by hand from numbered instructions with a "why" attached — enforced by a guard that blocks the AI from touching the editor. The full production layer comes along: a sharded game bible (vision, one file per mechanic, story shards), milestones with definitions of done, playtest capture, and a license-tracked asset manifest.

---

## The full capability list

### Core platform

- **Silos** — independent workspaces per domain (software, design, games, ideas, learning, career, knowledge), each with its own rules the AI follows automatically based on where you're working.
- **Plain-English commands** — 30+ conversational triggers (`standup`, `wrap up`, `spec checkout-flow`, `critique <url>`, `practice japanese`, `trade — …`). No syntax to memorize.
- **Hard gates, not reminders** — the defining feature. Rules that matter are enforced at the system level: no code before plan approval on big features, no source files without tests, no design handoff with critical issues open, no publishing before the confidentiality checklist, no secrets in files, no rewriting of journals. The AI cannot be talked past a gate.
- **Session memory** — every session starts with the right context injected (project status, your learned preferences, health warnings) under a strict token budget, and ends with a wrap that logs, syncs, and learns.

### Knowledge system

- **MewWiki** — an Obsidian vault that maintains itself: project mirrors, decision log with provenance (design decisions carry their Figma frame), meeting notes, a knowledge library. You browse; the AI writes.
- **Semantic memory** — everything is locally indexed (no cloud); past decisions and lessons resurface automatically when relevant. "What did we decide about X in March?" takes seconds, with sources.
- **Capture anywhere** — `dump — <thought>` mid-session, voice notes from your phone, document ingestion with proposed concept pages.

### Software delivery (for non-engineers leading engineering work)

- **Spec-driven pipeline** — your idea becomes numbered, testable acceptance criteria in product language; you approve *before* code exists; tests are derived from your criteria; "done" means the checks pass. You control quality without reading code.
- **CI safety net** — every project gets automated verification (types, lint, tests, build, dependency audit); you read green/red checks on GitHub.
- **Verified wrap-ups** — a session can't claim "done" over a failing build; it gets tagged incomplete with the failure as the next action.

### Design practice (built by a design lead, for design leads)

- **Enforced quality flow** — every UI change is checked against an anti-pattern blocklist in real time; a three-part pre-ship review (accessibility/performance scoring, copy check, ugly-data stress test) gates delivery.
- **Figma integration** — pull designs and variables, detect token drift between Figma and code, surface unresolved Figma comments in the morning standup.
- **`critique <any url>`** — structured, severity-ranked design review of any page, including competitors'.
- **One-command client handoff** — brief, design decisions with receipts, quality scores, and asset manifest in a single package.
- **Visual regression** — automatic screenshots diffed at session end, so unintended changes get caught.

### Health and observability

- **`mew doctor`** — 16 automated checks (configuration, token efficiency, hooks, stale projects, learning velocity) run at every session start; problems arrive as notifications before they cost a day.
- **`mew dashboard`** — one HTML page: every project with phase and idle time, health status, agent activity, learning tracks, and the skill compass.
- **Usage telemetry** — token spend and cache-efficiency reports; the system detects its own waste (it once caught a "compression" layer that was quietly multiplying costs).
- **`mew update`** — one-command safe upgrades: pulls, reinstalls, re-registers, verifies, and never touches your project data.

### Ownership and privacy

- **Plain local files, forever.** Markdown and JSON in git repos you control. No cloud, no lock-in — if the AI vanished tomorrow, everything remains readable.
- **Structural privacy.** Sensitive silos are excluded from search indexes and briefs; private repos never get remotes; publishing anything requires an explicit human checklist; nothing is ever posted or sent automatically.
- **Secrets discipline** — keys live in one gitignored place; writes containing credential patterns are blocked system-wide.

---

## Is it for you?

**Yes, if:** you use Claude Code (or want to) as a daily working partner; you care about quality enforcement more than raw speed; you want your knowledge, decisions, and growth to compound instead of evaporate; you like owning your data as plain files; you're growing beyond a single discipline and want a system that pushes you.

**Not yet, if:** you want a polished commercial app with support (this is a personal system you install and shape); you don't want a terminal anywhere in your workflow; or you need team/multi-user features — MewVault is deliberately single-player.

**Requirements:** a Claude subscription (Pro works — the system is aggressively token-efficient by design), Python 3.11+, Node, git, and optionally Obsidian (knowledge browsing) and Ollama (local semantic search). Setup is eight commands; the README walks through it.

---

*The one-line pitch: talk to it like a colleague, and it behaves like a whole team — a project manager who never forgets, a quality reviewer who can't be talked out of the checklist, a librarian who read everything you ever wrote, a tutor who explains as it builds, and a coach who notices when you've stopped growing. All in folders you own.*
