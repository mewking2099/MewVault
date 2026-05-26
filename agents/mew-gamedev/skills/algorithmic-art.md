---
name: algorithmic-art
triggers: [generative art, algorithmic art, flow field, particle system, create art using code, make generative art, p5.js]
description: Create algorithmic/generative art using p5.js with seeded randomness and interactive parameter controls. Two-step workflow: algorithmic philosophy then interactive HTML artifact. Use when the user wants living, code-driven visual art — not static design.
inject: on-trigger
claude_code_skills: []
source: anthropics/skills
---

# Algorithmic Art Skill

Two-step workflow: **Algorithmic Philosophy** → **p5.js Interactive Artifact**.

Output: `.md` (philosophy) + self-contained `.html` (interactive generative art).

---

## Step 1 — Algorithmic Philosophy

Create an ALGORITHMIC PHILOSOPHY — a computational aesthetic movement expressed through code.

### Name the movement
1–2 words: "Organic Turbulence" / "Quantum Harmonics" / "Emergent Stillness"

### Write the philosophy (4–6 paragraphs)
Address how the aesthetic manifests through:
- Computational processes and mathematical relationships
- Noise functions and randomness patterns
- Particle behaviors and field dynamics
- Temporal evolution and system states
- Parametric variation and emergent complexity

**Key requirements:**
- Each algorithmic aspect mentioned once — no repetition
- Stress mastery repeatedly: "meticulously crafted algorithm," "painstaking optimization," "master-level implementation," "refined through countless iterations"
- Leave creative implementation space — specific direction, not exact code

### Philosophy examples (condensed — actual output 4–6 substantial paragraphs)

**"Organic Turbulence"** — chaos constrained by natural law. Flow fields from layered Perlin noise. Thousands of particles following vector forces, trails accumulating into organic density maps. Color emerges from velocity — fast particles burn bright, slow ones fade. A meticulously tuned balance.

**"Quantum Harmonics"** — discrete entities exhibiting wave-like interference. Particles on a grid, phases evolving through sine waves. Constructive interference creates bright nodes, destructive creates voids. Simple harmonic motion generates complex emergent mandalas.

**"Stochastic Crystallization"** — random processes crystallizing into ordered structures. Randomized circle packing or Voronoi tessellation, evolving through relaxation algorithms. Organic tiling that feels both random and inevitable.

Save the philosophy as a `.md` file.

---

## Step 2 — Deduce the Conceptual Seed

Identify the subtle conceptual thread from the user's request. This is **not always literal** — it's a niche reference woven invisibly into the algorithm's parameters and emergent patterns. Like a jazz musician quoting another song — only those who know will catch it, but everyone appreciates the beauty.

---

## Step 3 — p5.js Interactive Artifact

Build a single, self-contained HTML file that works immediately in any browser or claude.ai. No external files except p5.js from CDN.

### Required structure

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.7.0/p5.min.js"></script>
  <style>
    /* Layout: sidebar left (320px), canvas right */
    /* Light background, clean sans-serif UI */
    /* Anthropic palette: #f5f1eb bg, #e8622a accent, #1a1a1a text */
  </style>
</head>
<body>
  <div id="sidebar">
    <!-- SEED SECTION (always include) -->
    <!-- Current seed display, Prev/Next/Random buttons, Jump-to input -->

    <!-- PARAMETERS SECTION (customize per artwork) -->
    <!-- Sliders with labels and live value display -->

    <!-- COLORS SECTION (optional — include if palette is adjustable) -->

    <!-- ACTIONS SECTION (always include) -->
    <!-- Regenerate, Reset, Download PNG buttons -->
  </div>
  <div id="canvas-container"></div>
  <script>
    // ALL p5.js code inline — setup(), draw(), classes
    // Seed-based randomness: randomSeed(seed); noiseSeed(seed);
    // Parameter object with defaults
    // UI event handlers
  </script>
</body>
</html>
```

### Seeded randomness (always required)

```javascript
let seed = 12345;
randomSeed(seed);
noiseSeed(seed);
```

Same seed → identical output every time.

### Parameter design

Define what's tunable based on the philosophy:
```javascript
let params = {
  seed: 12345,
  // quantities, scales, speeds, probabilities, ratios, angles, thresholds
  // e.g. particleCount: 1000, noiseScale: 0.003, speedMultiplier: 2.0
};
```

Don't think in terms of "pattern types" — think "what properties control this system?"

### Fixed vs. variable sections

**Always fixed (same across all artworks):**
- Sidebar layout structure
- Seed display + Prev/Next/Random/Jump controls
- Regenerate, Reset, Download buttons

**Always variable (unique per artwork):**
- The p5.js algorithm (setup/draw/classes)
- Parameter definitions and UI controls
- Colors section (include only if palette is adjustable)

### Algorithm approach

Let the philosophy dictate implementation — not a menu of patterns:
- Organic emergence → elements that accumulate, grow, interact over time
- Mathematical beauty → trigonometric functions, golden ratios, harmonic relationships
- Controlled chaos → variation within strict boundaries, bifurcation, phase transitions

### Craftsmanship requirements
Every parameter deliberately tuned. Balance complexity without visual noise. Thoughtful color palettes — not random RGB. Same seed → always identical output. Smooth performance if animated.

---

## Variations

Seed navigation (built into the sidebar) lets users explore variations without creating multiple files. If specific variations are requested: add seed presets or a gallery mode — all within the same artifact.

---

## MewVault Context

- Game experiments → `game-lab/_experiments/<name>/` (no MewKing gate)
- Production game assets → `game-lab/<project>/assets/`
- Philosophy `.md` → alongside the `.html` artifact in the same directory
- If this is a game UI or title screen element, align with mechanic-design notes in `wiki/`
