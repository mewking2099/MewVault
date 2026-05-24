# Game Lab Rules

You are working in `game-lab/`. These rules apply in addition to mew-common.

## Project layout

```
game-lab/
  _experiments/<name>/    # low-commitment prototypes
  <project>/
    Project_Status.md     # tier, current_phase, concepts_count, mechanics_count
    proposals/active/
    src/                  # GDScript / C# source
    assets/               # art, audio — never auto-generate large binaries
    raw/                  # design docs — immutable
    wiki/                 # mechanics and concept distillations
    log.md
```

## Godot conventions

- GDScript is the default. C# only if the user explicitly requests it.
- Node naming: PascalCase for nodes, snake_case for variables and functions.
- Signals before inheritance — prefer signals and composition over deep inheritance chains.
- Never write `.godot/` or `export/` — these are gitignored.

## Experiments vs projects

- `_experiments/` is for rapid prototypes. No MewKing gate required.
- Full game projects under `game-lab/<project>/` follow normal tier rules.
- Promote an experiment: `mew promote game-lab/_experiments/<name> --to game-project`.

## Mechanics tracking

- `mechanics_count` and `concepts_count` in Project_Status.md are maintained by Claude after each session.
- Increment them when a new mechanic or game concept is documented in `wiki/`.
