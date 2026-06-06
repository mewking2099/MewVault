---
name: godot-debug
triggers: [error in godot, godot crash, script error, invalid call, nil reference, node not found, godot isn't working, broken in godot]
description: Troubleshoot Godot runtime errors and GDScript bugs from pasted error output.
inject: on-trigger
---

# Skill: Godot Debug

## Error Protocol

When the user pastes an error, extract:
1. **Error type** — the first line (e.g. `Invalid call`, `Nil reference`, `Node not found`)
2. **File + line** — `res://scripts/Player.gd:42`
3. **Call stack** — which function triggered it
4. **Context** — what the user was doing when it crashed

Then diagnose and output a fix. Do not rewrite the entire script — only change the minimum lines needed.

---

## Common Godot 4 Error Patterns

### `Invalid get index 'X' on base 'Nil'`
Node reference is null. Cause: `@onready` var not found, wrong node path, or the node doesn't exist in the scene tree yet.
```gdscript
# Fix: check node path and use @onready correctly
@onready var player = $Player  # path must match scene tree exactly
```

### `Attempt to call function 'X' on a null instance`
Called a method on a node that is null. Same root cause as above — wrong path or node deleted.

### `Node not found: 'X'`
`$NodeName` path doesn't match the actual scene tree. Check PascalCase, correct parent, and that the node exists in the .tscn.

### Signal already connected
```gdscript
# Fix: check before connecting
if not body.is_connected("hit", _on_body_hit):
    body.connect("hit", _on_body_hit)
```

### `Cannot call method 'X' on a freed object`
Object was `queue_free()`'d but something still holds a reference. Use `is_instance_valid(obj)` before calling.
```gdscript
if is_instance_valid(enemy):
    enemy.take_damage(10)
```

### `Stack overflow`
Recursive function without a base case. Check `_process` or a signal that re-emits itself.

### Physics body not moving
- `CharacterBody2D` requires `move_and_slide()` — velocity alone does nothing
- `RigidBody2D` should not have its position set directly

### Animation not playing
- Check `AnimationPlayer` node name and animation name match exactly (case-sensitive)
- Confirm the AnimationPlayer is not paused (`paused` property)

---

## Debug Output Format

```
## Debug: <error type>

**Root cause:** <one sentence>
**Location:** <file>:<line>

**Fix:**
[code block — only the changed lines, with context]

**Why:** <one sentence explaining why this fixes it>

**Test:** <what to check after the fix to confirm it works>
```

---

## When the Error Is Not Clear

Ask for:
1. The full error text (not a summary)
2. The relevant script section (the function where the error occurs)
3. The scene tree for that node (what children it has)

Do not guess from incomplete information.
