---
name: godot-coder
triggers: [write the script, code the mechanic, implement in godot, write gdscript, add to player.gd, write the scene]
description: Write production-ready GDScript for Godot 4 mechanics — character movement, physics, signals, state machines, UI.
inject: on-trigger
---

# Skill: Godot Coder

Write GDScript for Godot 4. Always use Godot 4 API — never Godot 3 patterns.

---

## File Header Convention

Every script starts with:
```gdscript
extends <NodeType>  # e.g. CharacterBody2D, Node2D, Area2D

## <One-line description of what this script does>

signal <signal_name>(<params>)  # declare signals before vars
```

---

## Common Patterns

### CharacterBody2D — Movement + Jump
```gdscript
extends CharacterBody2D

const SPEED = 200.0
const JUMP_VELOCITY = -400.0
const GRAVITY = 980.0

func _physics_process(delta: float) -> void:
    if not is_on_floor():
        velocity.y += GRAVITY * delta

    if Input.is_action_just_pressed("ui_accept") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    var direction = Input.get_axis("ui_left", "ui_right")
    velocity.x = direction * SPEED

    move_and_slide()
```

### Area2D — Hitbox / Pickup Detection
```gdscript
extends Area2D

signal collected(value: int)

@export var value: int = 10

func _ready() -> void:
    body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        collected.emit(value)
        queue_free()
```

### State Machine (lightweight)
```gdscript
extends CharacterBody2D

enum State { IDLE, RUN, JUMP, FALL, DEAD }
var state: State = State.IDLE

func _physics_process(delta: float) -> void:
    match state:
        State.IDLE: _state_idle(delta)
        State.RUN:  _state_run(delta)
        State.JUMP: _state_jump(delta)
        State.FALL: _state_fall(delta)

func _change_state(new_state: State) -> void:
    state = new_state
```

### Timer — One-shot and Repeating
```gdscript
# One-shot: spawn enemies every 3s
func _ready() -> void:
    var timer = Timer.new()
    add_child(timer)
    timer.wait_time = 3.0
    timer.timeout.connect(_on_spawn_timer)
    timer.start()
```

### Signals — Connect in _ready, Emit in Logic
```gdscript
# Emitter
signal health_changed(new_health: int)

var health: int = 100:
    set(value):
        health = clamp(value, 0, 100)
        health_changed.emit(health)

# Receiver (in HUD or other node)
func _ready() -> void:
    $"../Player".health_changed.connect(_on_health_changed)

func _on_health_changed(new_health: int) -> void:
    $HealthBar.value = new_health
```

### @export — Tunable Values
```gdscript
@export var speed: float = 200.0
@export var jump_force: float = 400.0
@export_range(0, 100) var health: int = 100
@export var projectile_scene: PackedScene
```

### Autoload (Singleton) Pattern
```gdscript
# In Project Settings → Autoload: add GameState.gd as "GameState"
extends Node

var score: int = 0
var lives: int = 3

signal score_changed(new_score: int)

func add_score(amount: int) -> void:
    score += amount
    score_changed.emit(score)
```

---

## Rules

- Cache `get_node()` results in `_ready()` using `@onready`
- Never call `get_node()` inside `_process()` or `_physics_process()`
- Use `move_and_slide()` for CharacterBody2D — never set `position` directly in physics
- Declare signal types: `signal hit(damage: int)` not `signal hit`
- Use `is_in_group()` for broad collision checks, not `instanceof`
- `queue_free()` not `free()` — let the engine clean up safely

---

## Output Format

When writing a script:
1. Show the full file (not a diff) if it's new
2. Show only the changed function + surrounding 2 lines if modifying existing
3. State which node this script attaches to
4. State which signals it emits and which it listens to
5. Include one `print()` at the key action point so the user can confirm it fires

After writing, state: **"Paste this into `<NodeName>` in Godot and run. Report back what you see."**
