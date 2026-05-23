---
name: gdscript-review
triggers: [review this script, check the gdscript, godot code review, is this correct]
description: Review GDScript for Godot conventions and performance issues
inject: on-trigger
---

# Skill: GDScript Review

Review GDScript files for:

**Conventions:**
- Node names: PascalCase (`PlayerController`, `EnemySpawner`)
- Variables/functions: snake_case (`health_points`, `take_damage()`)
- Signals declared before `extends` or at top of class
- `@export` vars have type annotations
- No deep inheritance — prefer composition + signals

**Performance:**
- `_process` doing heavy computation every frame (should cache or use `_physics_process`)
- Allocating new objects in `_process` (use object pools)
- `get_node()` calls in `_process` (cache in `_ready()` instead)
- Large arrays iterated every frame without early exit

**Output:**
```
## GDScript Review: <filename>
- ✓ <what's good>
- ⚠ <warning>: <explanation>
- ✗ <issue>: <fix>
```
