# Subagent Model Routing

When spawning subagents via the Agent tool, select the cheapest model that can handle the task. Over-provisioning (Opus for file search) wastes tokens and increases latency.

## Model Selection Table

| Task type | Model | Reasoning |
|-----------|-------|-----------|
| Explore / search / grep | Haiku | Fast, cheap, good enough for finding files and patterns |
| Single-file edit with clear spec | Haiku | Mechanical task, no deep reasoning required |
| Multi-file implementation | Sonnet | Best cost/quality balance for coding |
| Architecture decisions | Opus | Needs to hold entire system model in context |
| Security analysis / audit | Opus | Cannot afford to miss vulnerabilities |
| PR / code review | Sonnet | Understands context, catches nuance |
| Documentation writing | Haiku | Structure is simple |
| Debugging complex bugs | Opus | Needs to trace across multiple files and states |
| Research / web search | Haiku | Retrieval, not reasoning |
| Test generation | Sonnet | Needs to understand behavior, not just syntax |

## MewVault Agent Defaults

| Agent | Default model | Override when | Dispatch via |
|-------|--------------|---------------|--------------|
| mew-chief | Sonnet | Complex cross-silo orchestration → Opus | Agent tool |
| mew-planner | Opus | Always — architecture is high-stakes | Agent tool |
| mew-coder | Sonnet | Simple 1-2 file changes → Haiku | Agent tool |
| mew-designer | Sonnet | — | Agent tool |
| mew-gamedev | Sonnet | — | Agent tool |
| mew-learner | Sonnet | — | Agent tool |
| mew-researcher | Sonnet | Architecture-level feasibility → Opus | Agent tool |
| mew-archivist | Haiku | Session wrap is mechanical | Agent tool |
| **mew-coder-simple** | **DeepSeek V3** | Pure generation, tight spec | **`mew dispatch`** |
| **mew-coder-reason** | **DeepSeek R1** | Logic-heavy, reasoning-first | **`mew dispatch`** |

## DeepSeek Dispatch Agents

`mew-coder-simple` and `mew-coder-reason` are **proxy agents** — they are NOT spawned via the Agent tool. They are called via `mew dispatch` through the LiteLLM proxy at localhost:4000.

**When to use mew-coder-simple (DeepSeek V3):**
Pure functions, API route handlers, DB queries, type definitions, config files, GDScript mechanics, shell/Python scripts, boilerplate following an established pattern. Anything where the spec is complete and the output contract is tight.

**When to use mew-coder-reason (DeepSeek R1):**
Algorithms, state machines, scoring/ranking logic, regex/parsers, performance optimization, math-heavy functions. Anything where the correctness must be derived before the code can be written.

**Dispatch pattern:**
```bash
cat > /tmp/task.md << 'EOF'
Language: TypeScript
Task: implement X with signature Y
Constraints: ...
Example: ...
EOF
mew dispatch --agent mew-coder-simple --task-file /tmp/task.md
```

## Rules

- **Default to Sonnet** for 90% of coding tasks.
- **Upgrade to Opus** when: first attempt failed and you're retrying, task spans 5+ files, architectural decision, security-critical code.
- **Downgrade to Haiku** when: searching/grepping, reading files to gather context, writing docs or comments, single mechanical change with no judgment required.
- **Never use Haiku** for: code that will run in production without review, security decisions, anything involving credentials or auth logic.

## Practical Pattern

```
Main task (Sonnet or Opus)
├── Search/explore subagent (Haiku) — "find all files that use X"
├── Implementation subagent (Sonnet) — "implement Y in these files"
└── Review subagent (Opus) — "security review of these changes"
```

The main context window stays clean; subagents consume their own context and return summaries.
