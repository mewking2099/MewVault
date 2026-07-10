# {{name}} — Architecture (living document)

> Read at every session start. Update whenever a system is added or changed.
> Code that contradicts this document is wrong — fix one or the other, explicitly.

## North star

<!-- One sentence: what this game is when it's done. -->

## System map

| Module (asmdef) | Responsibility | Talks via | Data assets |
|---|---|---|---|
| Core | shared types, event channel base classes | — | — |
| _(add modules as they're built)_ | | | |

## Event channels

<!-- Every SO event channel: name, payload, who raises, who listens. -->

| Channel | Payload | Raised by | Listened by |
|---|---|---|---|

## Scenes

- `Bootstrap` — loads persistent systems, then the first gameplay scene (additive).

## Decisions

<!-- Architecture decisions with dates and reasons. Newest on top. -->
