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

| Agent | Default model | Override when |
|-------|--------------|---------------|
| mew-chief | Sonnet | Complex cross-silo orchestration → Opus |
| mew-planner | Opus | Always — architecture is high-stakes |
| mew-coder | Sonnet | Simple 1-2 file changes → Haiku |
| mew-designer | Sonnet | — |
| mew-gamedev | Sonnet | — |
| mew-learner | Haiku | Deep concept analysis → Sonnet |
| mew-archivist | Haiku | Session wrap is mechanical |

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
