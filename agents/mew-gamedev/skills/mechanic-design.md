---
name: mechanic-design
triggers: [mechanic, game feel, how should the player, design the, prototype]
description: Design a game mechanic with feel notes and Godot implementation sketch
inject: on-trigger
---

# Skill: Mechanic Design

When asked to design or prototype a game mechanic:

1. **Define the mechanic** — one sentence: what does the player do, what happens.
2. **Game feel notes** — what should it *feel* like (snappy, weighty, floaty)?
3. **Godot sketch** — which nodes, signals, and script outline would implement this:
   - Node tree
   - Key signals
   - Core `_process` / `_physics_process` logic in pseudocode
4. **Edge cases** — what breaks this mechanic? What player behaviour exploits it?
5. **Wiki entry** — write to `<project>/wiki/mechanic-<name>.md` and increment `mechanics_count` in `Project_Status.md`.

Keep prototypes in `_experiments/` — no MewKing gate required there.
