# Unity in the game silo — workflow guide

Written 2026-07-08 for: Unity 6 Personal, 2D first project, owner has tinkered with Unity, learning-first. The enforced version of this lives in `.claude/rules/mew-game/unity-rules.md`; this doc is the human explanation.

## The model in one paragraph

MewVault writes every line of C#. You perform every editor action by hand, following numbered steps with a "Why:" explainer — that's where the learning happens. A Unity MCP bridge gives Claude *eyes* (scene hierarchy, console errors, test results) but the `unity-guard` hook blocks its *hands* — any MCP tool that would mutate the editor is rejected at the OS level and converted into manual steps for you. The whole game's structure lives in `wiki/architecture.md`, which Claude reads at session start and must keep updated, so it always codes against the full architectural picture, never just the file in front of it.

## One-time setup (~30 min)

**1. Unity Hub + Unity 6** — install Unity Hub from unity.com/download, then Installs → Install Editor → Unity 6 LTS. Include "Visual Studio Code support" if offered. Personal license is fine.

**2. Scaffold the MewVault project**
```bash
mew new game-project <name> --engine unity
```
Creates `game-lab/<name>/` with Project_Status.md (`engine: unity`), the living `wiki/architecture.md`, learning trackers, and a Unity .gitignore.

**3. Create the Unity project inside it** — Unity Hub → New Project → **2D (URP)** template → set Location to `~/Jan/game-lab/<name>/` and Project Name to match. Unity creates `Assets/`, `Packages/`, `ProjectSettings/` inside your MewVault project folder.

**4. Connect the MCP bridge (Claude's eyes)** — using CoplayDev's free bridge:
   - Unity: Window → Package Manager → + → "Add package from git URL" → `https://github.com/CoplayDev/unity-mcp.git?path=/UnityMcpBridge` (check the repo README for the current URL).
   - Terminal: `claude mcp add unity-mcp -- <command from the bridge's README>` (it prints the exact command after install).
   - Verify in a Claude session: "read the Unity console" should work; "create a cube" should be **blocked by the unity-guard hook** — if it isn't, run `mew doctor` and check hook registration.

**5. Git for Unity** — the scaffold's .gitignore covers Library/Temp/etc. Two Unity-specific settings are already default in Unity 6 (Visible Meta Files, Force Text asset serialization). For scene/prefab merge conflicts, configure UnityYAMLMerge once:
```bash
git config merge.unityyamlmerge.driver '"/Applications/Unity/Hub/Editor/<version>/Unity.app/Contents/Tools/UnityYAMLMerge" merge -p %O %B %A %A'
```

## The session loop

1. `cd ~/Jan/game-lab/<name>` → `claude` → say what you want ("add player movement").
2. Claude reads architecture.md, proposes the approach (tier rules apply — stalk = verbal approval).
3. **Code steps**: Claude writes the C# file(s), explains what each part does and why it's structured that way.
4. **Editor steps**: numbered manual instructions — exact menu path, what to verify when you run the scene, and the "Why:" concept explainer.
5. You do the step, run the scene, report. Errors → Claude reads the console via MCP and enters fix-mode (minimum change, no refactoring).
6. One step at a time — Claude stops after each and waits. This is mandatory silo discipline, not politeness.
7. `wrap up` at session end: log, architecture.md check, concepts/mechanics counts, wiki sync, commit suggestion.

`teach me <topic>` any time for a deep dive (explain → annotated example → contrast with the alternative → a try-it-yourself check → concept page archived to wiki/).

## The architecture you'll be learning

**ScriptableObject-driven, modular** — Unity's own recommended pattern for maintainable games, and unusually friendly to a designer:

- **Data as assets.** Enemy stats, player config, level definitions are ScriptableObject assets you edit in the Inspector — like design tokens, but for gameplay. Changing a value never touches code.
- **Event channels.** Systems never reference each other directly. When the player dies, the Health system raises a `PlayerDied` event channel (also an asset); UI, audio, and the game-over screen each listen independently. You can add or remove listeners without touching the sender — the same decoupling idea as pub/sub in design systems.
- **Assembly definitions per module.** Each feature (Movement, Health, Inventory…) compiles separately and may only depend on Core. Keeps compile times fast and makes dependencies explicit — the module table in architecture.md mirrors this exactly.
- **Thin MonoBehaviours.** Unity components handle input and lifecycle only; game logic lives in plain C# classes, which is what makes EditMode tests possible (and keeps the TDD gate meaningful).

Why not the alternatives: big "GameManager" singletons couple everything to everything (fast at first, unmaintainable by week three); full dependency-injection frameworks (VContainer/Zenject) are industry-real but add a layer of magic that hurts learning — worth revisiting on project #3.

## Beyond code: the production layer (added same day)

A game project is a sharded bible, not just code. Every project scaffolds with:

- `design/` — vision.md (pitch + 3 pillars, the only design file read every session), one shard per mechanic (`design/mechanics/<slug>.md` with status + module link), story shards (synopsis → characters/world/beats), levels, ui-ux.
- `production/` — backlog.md (Now max 3 / Next / Later, groomed at wrap), milestones.md (vertical slice → alpha → beta with definitions of done), playtests/ (immutable capture files).
- `assets/manifest.md` — every asset: status (needed/placeholder/final), source, license. Placeholder-first policy: mechanics are built with primitives; art is a manifest entry, never a blocker.

Token discipline is structural: Claude reads entry points (vision + the relevant `_index.md`) and then only the shards a task needs — never the whole tree; shards split at 150 lines. Total context comes from indexes + the living architecture.md, not from loading everything.

Workflows: `mechanic <name>` (design shard → acceptance criteria → approval → build → index updated), `playtest — <notes>` (verbatim capture → categorized extraction → backlog, with your confirmation), `backlog` or `game status` (one compact production view), `story session` (narrative work under shard discipline, decisions cross-linked to mechanics).

## Sources

Unity MCP: unity.com/blog/unity-ai-mcp-how-to-get-started · github.com/CoplayDev/unity-mcp · github.com/IvanMurzak/Unity-MCP
Architecture: unity.com/resources/create-modular-game-architecture-scriptableobjects-unity-6 · unity.com/how-to/scriptableobjects-event-channels-game-code · unity.com/how-to/organizing-your-project
