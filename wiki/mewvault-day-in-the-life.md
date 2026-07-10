# MewVault — how it works in daily life

*A plain-language guide to a personal AI workspace. Written to share — no confidential details inside.*

## What it is, in one paragraph

MewVault is a personal workspace built on top of an AI coding assistant (Claude Code). All work lives in organized folders called **silos** — one for design projects, one for software, one for games, one for ideas, one for learning. The AI reads the right context automatically when a session starts, does the heavy lifting during the day, and writes everything worth keeping into a knowledge base at the end. You talk to it in plain English. No commands to memorize.

## The three ideas that make it work

**1. Silos.** Every kind of work has its own home with its own rules. A design project follows design rules (quality checklists, Figma links). A software project follows engineering rules (specs before code, tests before features). The AI behaves differently depending on where you are — like a colleague who knows which hat to wear.

**2. Plain English in, real work out.** You type things like *"standup"*, *"wrap up"*, *"spec user-login"*, or *"critique this design"* — and a full workflow runs. Example: typing *"brief onboarding"* makes the system search everything ever written about onboarding — past decisions, meeting notes, specs — and hand back a one-page summary with sources.

**3. Gates, not reminders.** The most important rules are enforced by the system, not by memory. The AI physically *cannot* write code for a big feature before the plan is approved. It *cannot* mark a design "ready for handoff" while serious quality issues are open. It *cannot* skip writing a test. Rules that matter are walls, not sticky notes.

## A typical day

**Morning.** Open a terminal, type **standup**. You get one screen: today's meetings, active projects and their next steps, open items, and anything waiting for review. Two minutes, and the day has a shape.

**During work — design example.** Type *"design session website-refresh"*. The system loads the project's design context, checks the product brief exists, and pulls the latest from Figma. While working, every visual change is automatically checked against a quality blocklist (no trendy-but-bad patterns allowed). Before anything is called done, a three-part quality review runs: accessibility and performance scoring, copy check against the audience, and stress-testing with ugly real-world data (very long names, error states). The scores are saved — and the project can't move to handoff while critical issues remain open.

**During work — software example.** Type *"spec payment-reminders"*. The AI drafts a specification with numbered, testable acceptance criteria — in product language, not code. Work stops until you approve them. Then tests get written *from* your criteria, then code until the tests pass. At the end you read "AC-1 ✓ AC-2 ✓" and a green check on GitHub — you verified the work without reading a line of code.

**Capturing thoughts.** Mid-anything, type *"dump — we decided to use the simpler nav pattern"*. The system classifies it (a decision), files it with its source, and it becomes searchable forever. On the go, a voice note on your phone lands in the same inbox automatically.

**Evening.** Type **wrap up**. The system writes the session log, updates project status, runs the quality checks one more time, asks *"did I get anything wrong today that I should learn from?"* (corrections you confirm become permanent behavior), syncs everything to the knowledge base, and suggests a commit message. Next morning, it remembers all of it.

## The silos, one by one

**Design studio.** Projects with Figma integration, enforced quality gates, and a one-command client handoff package (brief + design decisions + quality scores + asset list). Also: *"critique <any URL>"* gives a structured design review of any page — including competitors'.

**Software projects.** Spec-driven: idea → acceptance criteria you approve → tests → code → automated verification. Built so a non-engineer can lead engineering work safely, because every checkpoint is readable in plain language or as a green/red check.

**Game lab.** Learning-first game development: the AI writes all the code and explains it; you do every game-engine step by hand from numbered instructions with a "why" attached — so you actually learn. The game's design, story, mechanics, backlog, and asset list all live as small linked documents, so nothing exists only in someone's head.

**Idea hub.** Rough ideas go in; *"validate <idea>"* runs a market scan — competitors, effort estimate, a pursue/park/kill recommendation with sources. Ideas graduate to real projects only when validated. No more idea graveyard, no more building the wrong thing for a month.

**Learning lab.** Structured skill tracks (a language, a technical skill — anything). Daily 20-minute practice sessions with spaced repetition handled by a scheduler, one new concept per session, and progress that shows up in the morning standup. The system protects the streak, because daily-and-small beats rarely-and-big.

**Career studio.** Case studies assemble themselves from real project records — the decisions, the process, the outcomes — then go through your personal voice edit and a confidentiality check (every client name and internal number is reviewed before anything can be marked shareable). Plus a living CV, a skill matrix where every claimed skill needs linked evidence, and monthly mock interviews that quiz you on your *actual* past decisions.

**Ops hub (work operations).** The day-job companion: running 1:1 agendas that build themselves from notes between meetings, feedback logs, goal tracking, and quarterly review drafts assembled from a whole quarter of real observations. Kept in a private, extra-protected area — people-related notes never leak into searches or shared documents.

**Content studio.** Turns weekly learnings into publishable posts, written in your voice, formatted for the platform. Everything passes the same confidentiality check. Publishing is always manual — the system never posts anything by itself.

## The safety net (always on)

- A **health monitor** runs 15+ checks at the start of every session — is anything misconfigured, wasteful, or stale? Problems arrive as a notification before they cost a day.
- A **dashboard** shows every project, its phase, how long it's been idle, and its quality scores — one page, always current.
- Everything lives in **plain local files** you own. No cloud lock-in. If the AI vanished tomorrow, every document, decision, and log would still be there, readable.
- **Privacy is structural**: sensitive areas are excluded from search indexes; publishing anything requires an explicit human check of names and numbers; nothing posts or sends without confirmation.

## What compounds over the long term

Month by month, the system gets more valuable in four ways:

1. **Memory.** Every decision, lesson, and gotcha is searchable. "What did we decide about X last spring?" takes ten seconds, with sources — instead of an hour of digging or a wrong guess.
2. **Behavior.** Every correction you confirm becomes a permanent rule. The assistant in month six makes fewer of the mistakes it made in month one.
3. **Evidence.** Case studies, skill records, review material, and interview practice accumulate as a side effect of normal work. When an opportunity appears, the portfolio is already written.
4. **Skills.** The learning tracks and the learn-by-building workflows mean the human is growing alongside the system — the point is not to outsource thinking, but to compound it.

## The one-line summary

Talk to it like a colleague, and it behaves like a whole team: a project manager who never forgets, a quality reviewer who can't be talked out of the checklist, a librarian who read everything you ever wrote, and a tutor who explains as it builds — all working out of folders you own.
