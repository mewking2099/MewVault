# Silo: game-lab — Game Development

Engine: Godot 4 (locked). GDScript. Scene/node model.

## Structure

```
game-lab/
├── _experiments/      # throwaway prototypes — no tracking overhead
└── <project>/
    ├── Project_Status.md
    ├── CLAUDE.md
    ├── concepts-learned.md   # engine concepts, GDScript, node types
    ├── mechanics-built.md    # what's been shipped: feature (session NN)
    └── <godot project files>
```

## Rules

- Check `mechanics-built.md` before implementing any mechanic — don't rebuild solved problems.
- `/teach godot` activates pedagogical mode (registry-first, 5-step cap, why-before-what).
- Without `/teach`, game-lab is treated as normal coding context.
- Experiments: `mew new game-experiment <name>`. Promote with "promote this experiment".
- `/wrap` after a game session: update `mechanics-built.md` with what shipped.
