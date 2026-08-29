# Graph-Loop Engineering — Plain English Guide

_What we built, how it works, and where it goes next._

---

## The big picture in one paragraph

MewVault used to route every AI task to the same model and forget the result the moment the conversation ended. Now it does four things it didn't do before: it **picks the right AI model automatically** (and a free one when possible), it **writes down every AI call** so you can audit and learn from them, it **uses the shape of your codebase** to predict how risky or complex a task is before running it, and it **runs multi-step loops safely** without getting stuck in an infinite cycle.

---

## How the whole thing flows — the simple version

```
You type a task
       ↓
mew dispatch:  "what kind of task is this?"
       ↓
Route prediction: "how complex? how many files affected?"
       ↓
Pick the right model (free GLM or Anthropic, based on task type)
       ↓
Call the model → get a response
       ↓
Write everything to the ledger (the permanent record)
       ↓
If this is a multi-step job → start a Loop
       ↓
Each loop tick: check predicate → livelock guard → write tick → repeat
       ↓
Loop terminates cleanly (done) or safely (stuck cap hit)
```

---

## Feature 1 — GLM models via Z.ai (free AI tier)

### What is GLM?

GLM (General Language Model) is a family of AI models made by Zhipu AI. They are available through a service called Z.ai. The important thing for MewVault: Z.ai has a **Coding Plan** — a flat monthly rate with no per-token billing. That means running thousands of code-review or ideation calls costs the same as running ten.

### What models do we use?

| Model name (internal) | What it's good at |
|---|---|
| `glm-code-reviewer` | Reading code, spotting bugs, security issues, explaining what code does |
| `glm-coder` | Writing code, implementing features, fixing bugs |
| `glm-ideator` | Generating new ideas, brainstorming |
| `glm-critic` | Challenging ideas, stress-testing, devil's advocate |

### Why does this matter?

Before this, every task — even a quick "does this look right?" — went to Anthropic's Claude and consumed tokens you pay for. Now, review and ideation tasks are routed to GLM for free, and Anthropic models handle only the tasks that need their specific strengths.

---

## Feature 2 — `mew dispatch` with auto-routing

### What is a dispatch?

A **dispatch** is simply "sending a task to an AI model and getting a response." `mew dispatch` is the command that does this for you — you give it a task description and it figures out the rest.

### How does auto-routing work?

The system reads your task description and looks for **signal words**:

- Words like `review`, `audit`, `check`, `inspect`, `security`, `lint` → route to `glm-code-reviewer`
- Words like `implement`, `write`, `build`, `fix`, `refactor` → route to `glm-coder`
- Words about ideas or reasoning → route to Anthropic models

This is called **keyword scoring** — it counts how many review signals vs. coder signals appear in your task, and the higher score wins. No machine learning involved; just a list of words and a counter.

### What you actually type

```bash
mew dispatch "review dispatch.py for security issues"   # → glm-code-reviewer (free)
mew dispatch "implement the new sort function"           # → glm-coder (free)
mew dispatch "architect a caching layer"                 # → Claude Sonnet or Opus
```

---

## Feature 3 — `mew ideate` (dual-model debate)

### The problem with asking one model

If you ask one AI "is this a good idea?", it tends to either say yes or say no. You get one perspective. There's no pushback, no devil's advocate, no independent second opinion.

### The dual-model debate

`mew ideate` runs a **three-round structured debate**:

**Round 0 — Parallel pitch:** Two models answer independently at the same time.
- GLM-5.2 gives its take
- Claude Opus gives its take
- They don't see each other's answers yet

**Round 1 — Cross-critique (parallel):** Each model reads the other's Round 0 answer and critiques it.
- GLM-5.2 reads what Opus said and challenges it
- Opus reads what GLM said and challenges it
- Both critiques happen at the same time (faster)

**Round 2 — Synthesis:** Opus alone reads both Round 0 answers and both critiques, then writes a final synthesis that resolves the disagreement.

### Why this helps

Ideas that survive critique from an independent model are more robust. You catch blind spots neither model would notice on its own. And because Round 0 and Round 1 are parallel, the full debate takes only slightly longer than asking one model twice.

---

## Feature 4 — The dispatch ledger (permanent record)

### What is a ledger?

A **ledger** is an accounting term — a permanent book of transactions. In MewVault, the dispatch ledger is a database file that records every AI call ever made: when it happened, what task was sent, which model answered, how long it took, whether it succeeded.

### The technology: SQLite

**SQLite** is a database that lives in a single file on your computer — no server needed, no setup. It speaks a language called SQL (Structured Query Language) that lets you ask questions like "show me all dispatches from last week" or "which agent had the most failures?".

We use SQLite in **WAL mode** (Write-Ahead Log). Think of WAL as a scratch pad: new writes go to the scratch pad first, then get merged into the main file. This means you can read the ledger while a dispatch is being written — they don't block each other.

### What gets recorded

Every dispatch row captures:
- `task_hash` — a fingerprint of the task (so duplicates are detectable)
- `agent` — which AI agent handled it
- `model_run` — the exact model used
- `outcome_class` — did it succeed, fail, or was it a test run?
- `predicted_radius` — how many files we thought the task would touch
- `actual_radius` — how many files it actually touched
- `complexity_score` — a number measuring how complex the task was
- `graph_epoch` — which version of the knowledge graph was active

### How to use it

```bash
mew ledger tail          # last 20 dispatches
mew ledger stats         # breakdown by agent and outcome
mew ledger migrate       # apply schema upgrades without losing data
```

---

## Feature 5 — Route prediction and shadow mode (Phase 2)

### What is shadow mode?

Before committing to a routing decision, you can run it in **dry-run** (shadow) mode:

```bash
mew route dry-run "refactor the auth module"
```

This tells you: "If you ran this task right now, it would go to `glm-coder`, blast radius = medium (≈14 files affected), complexity = 6.2." No model is actually called; it's a prediction only.

The prediction is written to the ledger. When you later run the real dispatch, the system compares the prediction to what actually happened — this is called **reconciliation**. Over time, you can see how accurate the predictions are.

### What is graph confidence?

The system also tells you how much it trusts its own routing predictions. This is called the **confidence bucket**:

| Confidence | Meaning |
|---|---|
| `high` | The knowledge graph has many nodes AND many connections — routing is well-informed |
| `medium` | Graph exists but sparse — routing is reasonable |
| `low` | Graph has nodes but no connections — keyword routing only |
| `insufficient` | Graph is too small to be useful |

If confidence is `low` or `insufficient`, the system still routes (using keywords), but it warns you.

---

## Feature 6 — Graph-aware routing (Phase 3)

### What is a knowledge graph?

A **knowledge graph** is a map of your codebase. Each file, function, or concept is a **node** (a dot on the map). When two things are connected — say, a function that calls another function — there's an **edge** (a line between dots).

MewVault uses a tool called **graphify** to build this map automatically by reading your source code.

### Blast radius

**Blast radius** is the answer to: "If this task goes wrong, how much of the codebase gets affected?"

The system finds the nodes your task keywords match (these are called **seed nodes**), then walks two hops outward along the edges. The total number of nodes in that neighborhood is the blast radius.

| Bucket | What it means |
|---|---|
| `small` | ≤5 files likely touched — low risk, fast to review |
| `medium` | 6–20 files — moderate scope |
| `large` | 21+ files — architect-level change, needs a plan |

### Complexity scoring

**Complexity** is not the same as size. A task that touches 3 files in 3 different modules is more complex than one touching 10 files all in the same module.

The formula:

```
complexity = file_count × log₂(community_span + 1) × type_diversity
```

Plain English:
- `file_count` — how many files are in the neighborhood
- `community_span` — how many distinct clusters of code are involved (more clusters = more complex)
- `type_diversity` — how many different kinds of nodes appear (functions, classes, config files, etc.)

A score above 20 (or more than 15 files) → `complex`. Otherwise `simple`.

### Capability edge registry

The system knows what each agent is good at. For example:

- `mew-coder-reason` → good at complex, large-radius tasks of class `implementation`
- `glm-code-reviewer` → good at small-radius tasks of class `review`
- `mew-planner` → good at architecture tasks regardless of radius

When the keyword routing picks an agent but the graph says the task is large and complex, the capability registry can **refine** the choice — but it can only pick agents whose task class matches. A review task never gets routed to a coder just because the files are complex.

---

## Feature 7 — Loop primitives (Phase 4)

### What is a loop in this context?

A **loop** is when the system runs the same kind of check repeatedly until a goal is met. For example: "keep checking whether all tests pass and the log is updated — stop when both are true."

Loops are useful for **end-of-session wrap** (did I write the log? did I write the brief?) and **spec-driven builds** (are all acceptance criteria ticked off?).

### The four loop types

| Loop type | Stops when... | Max ticks (attempts) |
|---|---|---|
| `wrap_prime` | `log.md` was updated this session AND the next-session brief file exists | 4 |
| `spec_build_verify` | All spec criteria are checked off AND tests pass | 8 |
| `plan_approve_execute` | Plan is approved AND all deliverables are checked off | 6 |
| `idea_lifecycle` | The idea's status is `promoted` or `archived` | 12 |

A **tick** is one iteration — one check of the predicate. The loop runs at most `max_ticks` times then terminates automatically, even if the goal was never met.

### What is a predicate?

A **predicate** is just a yes/no question the loop asks each tick: "is the goal met?"

For `wrap_prime`: "Is the log file's last-modified time newer than when this session started, AND does the brief file exist?"

For `spec_build_verify`: "Are all `- [x]` checkboxes ticked in the spec AND is there a `.tests-pass` marker file?"

### Livelock detection — what does "stuck" look like?

**Livelock** is when a loop keeps running but nothing changes. It's different from being slow — it's being busy but making zero progress.

Detection is two-part:

1. **Content hash streak:** If the output of tick N, tick N-1, and tick N-2 are all byte-for-byte identical (same hash), that's 3 consecutive no-progress ticks → loop terminates with `no_progress_cap` and escalates to you with a diagnostic dump.

2. **Graph-cycle prefilter:** The ledger checks whether the same loop is appearing in dispatch chains (loop calls dispatch, dispatch triggers loop again). This is additive evidence — it strengthens the case but doesn't trigger termination on its own.

### Provenance injection for briefs

When a `wrap_prime` loop completes successfully, it prepends a **provenance header** to the brief file:

```
<!-- provenance: loop_id=abc123, tick=2, generated=2026-08-29T14:30Z,
     advisory=true, note=contradiction-check against MASTER_SPEC required before use -->
```

This marks the brief as **advisory** — it was generated by an automated loop and must be checked against MASTER_SPEC before being treated as authoritative. This prevents auto-generated briefs from silently overriding human decisions.

---

## How it all fits together — the full flow

```
You run: mew dispatch "review auth.py for security holes"
                  │
                  ▼
        Keyword scoring:
        "review" + "security" → review_score wins
                  │
                  ▼
        Graph lookup:
        auth.py → seed nodes → 2-hop BFS → 8 nodes
        blast_radius = "small", complexity = 3.1
                  │
                  ▼
        Capability check:
        task_class = "review" → only review agents considered
        → glm-code-reviewer selected
                  │
                  ▼
        Confidence check:
        graph has edges → confidence = "medium"
        (no warning printed)
                  │
                  ▼
        Call Z.ai / GLM-5.3
        (free tier, no per-token cost)
                  │
                  ▼
        Write to ledger:
        task_hash, agent, model_run, predicted_radius=8,
        complexity_score=3.1, confidence_bucket="medium",
        outcome_class="success"
                  │
                  ▼
        Reconcile prediction (if dry-run was run earlier):
        predicted=small, actual=small → no divergence
```

For a multi-step job, the dispatch is followed by a loop:

```
mew loop start wrap_prime --task "end session"
        │
        ▼
   Tick 0: bootstrap (no predicate check yet)
        │
        ▼
   Tick 1: is log.md updated? is brief file present?
           No → record tick, continue
        │
        ▼
   (you write log.md and the brief)
        │
        ▼
   Tick 2: is log.md updated? is brief file present?
           Yes → TERMINATED(predicate_met)
           → provenance header injected into brief
```

---

## Future scaling

### Phase 5 — Fuzzy predicates

Right now, loop predicates are hard binary checks: "does the file exist?" and "is the checkbox ticked?". Phase 5 adds **fuzzy predicates** — soft scoring that can say "80% done" rather than just "not done." This allows loops to provide partial-progress feedback and make smarter decisions about when to escalate vs. retry.

### Kuzu graph database (when graphify hits its limits)

SQLite is great for the ledger, but graphify's `graph.json` is a flat file. When the codebase grows to tens of thousands of nodes and the BFS neighborhood expansion becomes slow, the plan is to migrate to **Kuzu** — an embedded graph database (like SQLite but designed for graphs). Kuzu speaks Cypher (a graph query language) and handles million-node graphs efficiently. The migration trigger: `graphify query` taking over 2 seconds consistently, or graph.json exceeding 50MB.

### Adaptive routing thresholds (§D-3)

Right now, blast-radius buckets (`small < 6 files`, `medium 6–20`, `large 21+`) are fixed. Future work: these thresholds adapt per-silo based on ledger history. A silo where "medium" tasks consistently turn into large actual impacts would automatically tighten its `medium` ceiling. This is heuristic adjustment — no model training, just threshold arithmetic on recorded outcomes.

### Cross-silo federation

Today, graph-aware routing reads from one silo's `graphify-out/graph.json`. The `cross_silo_read` table in the ledger already records when a task touches another silo's graph. The next step: `mew route` aggregates cross-silo graphs so that a task spanning `software-projects/` and `design-studio/` gets a unified blast-radius estimate.

### Capability edge integration into graphify

The `capability-edges.json` file (which agent handles which graph node types) is currently stored separately. When graphify adds support for incremental edge injection, capability edges will be first-class edges in the graph — meaning "mew-coder handles module_X" becomes a query-able relationship, not a separate file.

### Doobidoo vector rerank (Stage 2 retrieval)

Route prediction currently uses graph BFS (Stage 1). Stage 2 — semantic vector search via doobidoo — will rerank the neighborhood results by semantic similarity to the task description. This means "refactor authentication" matches `auth_middleware.py` even if the word "auth" doesn't appear in the node label.

---

## Glossary

| Term | Plain English meaning |
|---|---|
| **Dispatch** | Sending a task to an AI model and collecting the response |
| **Ledger** | A permanent, append-only record of all dispatches |
| **SQLite** | A database in a single file — no server required |
| **WAL** | Write-Ahead Log — a technique that lets reads and writes happen simultaneously without blocking |
| **schema_epoch** | A version number that tracks the database structure — bumped when columns are added |
| **Knowledge graph** | A map of your codebase where files/functions are dots and relationships are lines |
| **Node** | A dot on the knowledge graph — a file, function, class, or concept |
| **Edge** | A line between two nodes — means they are connected (one calls the other, one imports the other) |
| **BFS** | Breadth-first search — "walk outward from a starting point, one hop at a time" |
| **Blast radius** | How many nodes/files a task could affect if it goes wrong |
| **Complexity score** | A number measuring how spread across the codebase a task is |
| **Confidence bucket** | How trustworthy the routing prediction is (`high/medium/low/insufficient`) |
| **Predicate** | A yes/no question the loop asks each tick — "is the goal met?" |
| **Tick** | One iteration of a loop — one predicate check |
| **Livelock** | A loop that's running but making no progress — same output three ticks in a row |
| **Provenance** | A record of where something came from and how it was created |
| **Advisory** | Generated automatically — must be checked by a human before treating as authoritative |
| **graph_epoch** | A version counter for the knowledge graph — all routing decisions are pinned to an epoch |
| **Capability edge** | A recorded fact about which agent handles which kind of node type and task class |
| **Fuzzy predicate** | A predicate that returns a score (0–1) instead of just yes/no — Phase 5 |
| **Kuzu** | A graph database designed for large graphs — planned upgrade from flat JSON |
| **Dual-model debate** | Running two different AI models on the same question and having them critique each other |
| **Synthesis** | The final step of a debate — one model reads all the arguments and writes the conclusion |
| **graph_cycle** | A loop that calls a dispatch that triggers the same loop — detected as livelock evidence |
