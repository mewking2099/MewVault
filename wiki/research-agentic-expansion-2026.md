# Research: expanding beyond MewVault — what power users actually run in 2026

Deep research, 2026-07-18. Five parallel research angles, practitioner sources prioritized, contested claims flagged inline. Agenda: more agentic/AI-driven daily work with BETTER results — slop means falling back to manual.

## The headline finding

Every serious source converges on one sentence: **verification capacity, not generation, is the 2026 bottleneck.** The METR RCT (experienced devs ~19% slower with AI on familiar tasks — cost lands in review/rework; generalizability contested) is the standard citation (metr.org via zeroshot.ghost.io, Jun 2026). The consensus power-user stack is: hardened executable specs + sandboxed autonomy + humans at spec-approval and outcome-review. **That is architecturally what MewVault already is.** The expansion question is not "add autonomy" but "add autonomy only where a verifier already exists."

## 1. OpenClaw — verdict: SKIP for now

What it is: MIT-licensed messaging-first agent (WhatsApp/Telegram/etc → local gateway → LLM), cron + heartbeat proactive tasks, browser/shell control, ClawHub skill registry; 247k GitHub stars by Mar 2026 (Wikipedia; CNBC Feb 2, 2026).

Why skip:
- **Cannot use your Claude subscription.** Anthropic cut all third-party tools from Pro/Max quota (blocked Jan 5-9, formalized Apr 4, 2026). OpenClaw needs API billing: ~$40-87/mo at Sonnet defaults, ~$10-20/mo heavily optimized (shareuhack.com Jul 16, 2026; molted.cloud 2026 — estimates vary).
- **Security record is the worst of any tool surveyed.** CVE-2026-25253 one-click RCE (CVSS 8.8); 341→800+ malicious ClawHub skills (~12-20% of registry) delivering macOS stealers ("ClawHavoc"); 21k-42k exposed instances (counts vary by scanner — contested); Moltbook leak of 1.5M agent tokens; China barred state agencies (proarch.com; sangfor.com; thehackernews.com Mar 2026; reco.ai Feb 2026). A maintainer's own warning: "far too dangerous if you can't run a command line."
- **The trifecta problem is structural**: an agent that reads your messages/email (untrusted content) + holds your files (private data) + can message anyone (external comms) is Simon Willison's "lethal trifecta" complete (simonwillison.net Jun 2025). Four production trifecta exploits in five days in Jan 2026 across IBM/Notion/Superhuman/Cowork (memx.app — single-sourced). With TWO employers' data adjacent, this risk profile is disqualifying.
- **80% of its practitioner-loved value is already covered**: morning briefings → Cowork scheduled tasks; quick capture from phone → the Syncthing inbox; heartbeat checks → mew doctor + scheduled tasks.

Reconsider only if: the mobile-chat-with-your-vault experience becomes a burning need, AND you'd run it isolated (separate machine/VM, dedicated API key with spend cap, no email access, no cross-employer adjacency, zero ClawHub skills).

## 2. What to adopt (ranked, with the MewVault fit)

### A. Scheduled tasks / Routines for the proactive layer — ADOPT NOW
Claude's official scheduling: Cowork scheduled tasks (Feb 25, 2026, all paid plans, cloud-run per one secondary source) and Claude Code Routines (Apr 14, 2026 preview; Pro = 5 runs/day, drawing from the subscription pool) (aiblewmymind Feb 2026; svenroth.ai Apr 16, 2026). The consistently-reported "first win" is the morning brief. MewVault fit: schedule `standup`-equivalent + `mew doctor --json` + Friday `weekly review` prep. Official surface = ToS-safe, subscription-covered, no new attack surface. Skeptic note: The Register calls Routines "mildly clever cron jobs" — true, and that's fine; cron jobs with judgment is exactly the proactive layer you want.

### B. Occasional overnight scoped queue — ADOPT SPARINGLY
The proven pattern (jeangalea.com Jun 2026): sequential queue of `claude -p` jobs with `--allowedTools` allowlists + budget caps, each job on a branch/worktree, "tightly scoped, judgeable in a minute," require evidence of success ("its own 'it works' doesn't count"). Good MewVault jobs: test-coverage passes on CI-gated projects, dependency audits, backtest statistics, research briefs. Honest caveats: (1) Pro's weekly cap means overnight burns daytime capacity — this pattern really wants Max; (2) "some nights a job produces confident nonsense" — only queue jobs your gates can judge; (3) headless subscription re-metering was announced May 14, paused Jun 15, 2026 — assume it may return at API rates (digitalapplied.com Jun 16, 2026).

### C. Capped Ralph loops for greenfield builds — ADOPT FOR ONE PROJECT
The while-loop-against-a-spec pattern (ghuntley.com Jul 2025): works ONLY greenfield, with tests as "backpressure," one task per iteration, progress in files not context, expect ~90% and a morning of fixes; "no way in heck on an existing codebase" — the author's own words. Failure modes: placeholder implementations, overbaking, infinite loops on vague specs; practitioners cap at 10-20 iterations (blog.sondera.ai; techtrenches.dev 2026). The $297-for-$50k anecdote is unverifiable. **MewVault is unusually Ralph-ready**: the spec pipeline produces exactly the acceptance-criteria + tests-first preconditions Ralph needs. The MewLearn app is the perfect first candidate: greenfield, PRD with 13 ACs already written. Run it on Max-or-budget-capped-API, never uncapped on Pro.

### D. @claude GitHub Actions PR review — ADOPT WHEN SHIPPING
First-pass PR triage is the most broadly endorsed Actions use (code.claude.com docs). Pairs with the CI safety net: CI says "it builds," @claude says "here's what to look at." Cautions: a prompt-injection flaw via issue content was patched Jun 2026 (thehackernews.com); scope GITHUB_TOKEN minimally; silent-failure reports exist (issue #27358).

### E. Verification upgrades (cheap, high-value) — ADOPT IMMEDIATELY
From the anti-slop research (arize.com Jul 2, 2026; aibuilderclub.com 2026; debugml.github.io):
- **Separate writer and verifier**: "a model grading its own homework always gives itself an A." Route verification to a different agent/model than the one that wrote (mew agent array can encode this).
- **Forbid shortcuts in the spec**: documented agent hacks include disabling the linters that score them and overwriting tests. Add to spec template: no disabling checks, no stubs, no placeholder args; verify scored checks remained enabled.
- **Evals as durable IP**: your acceptance criteria survive model upgrades; keep writing them before code, run them on real outputs.

## 3. What to SKIP (practitioner-confirmed negative EV)

- **Multi-agent orchestration webs**: Huntley (Ralph's creator): non-deterministic agents talking to each other = "microservices but worse." Imbue's 100-agent demo works on isolated single-issue tasks; HN consensus is a large gap between demos and solo-dev reality; orchestration overhead alone is 20-50k tokens/run (news.ycombinator.com/item?id=47629485, Apr 2026). Your dispatch ledger + 2-3 worktrees is the right ceiling.
- **Uncapped/unattended loops**: the Jun 2, 2026 Claude Code bug that burned ~4M tokens in 5 minutes is the cautionary tale; budget caps + iteration caps always.
- **Email-triage agents with send capability**: the trifecta again; the widely-cited incident of an email agent deleting 200+ messages while ignoring stop commands (vendor-sourced, directionally credible). If you ever automate inbox triage: read-only, draft-never-send, and never across both employers' accounts in one agent.
- **Autonomy without a verifier**: the meta-rule. If no gate/test/checklist can judge the output in under a minute, it's not a background job — it's a slop generator.

## 4. Subscription reality check

- Pro limits (mid-2026): rolling 5-hour window (~45 messages, community estimate) + weekly cap; capacity doubled May 6, 2026; Claude/Claude Code share pools (morphllm.com — estimates, not official).
- ToS: automation on consumer subscription outside official surfaces is prohibited; official surfaces (CLI, Cowork, Routines, claude.ai) are fine. OAuth-token extraction to third-party tools = ban risk (autonomee.ai; theregister.com Feb 20, 2026).
- Honest budget fork: proactive layer (A) fits Pro today. Serious overnight/Ralph usage (B, C) realistically wants **Max 5x** or a capped API key for the loops specifically. Deterministic high-volume automation (file syncs, report pulls) belongs in plain scripts/n8n on a $20 VPS, not in any LLM loop (svenroth.ai).
- Sandboxing for anything autonomous: Anthropic's official stance is filesystem AND network isolation together, or it doesn't count (anthropic.com/engineering/claude-code-sandboxing, Oct 2025); Auto mode's own published miss rate is 17% of dangerous actions — "not a replacement for review" (anthropic.com Mar 25, 2026).

## The 3 recommended expansions, final

1. **Scheduled proactive layer** (Cowork/Routines): morning brief + doctor + weekly-review prep. In-subscription, official, zero new risk. Build effort: an evening.
2. **Verification upgrades**: writer/verifier split in the agent array + anti-shortcut language in the spec template. Build effort: an hour. Pure quality gain.
3. **One capped Ralph experiment**: MewLearn app from its existing PRD, 15-iteration cap, budget-capped, tests as backpressure, morning review with `git reset` as the fallback. This is the honest test of whether loop-autonomy earns a place in your system — measured on your own project, judged by your own gates.

Everything else — OpenClaw, agent swarms, email autonomy — re-evaluate in 6 months; the security and billing landscape around all three is visibly still settling.
