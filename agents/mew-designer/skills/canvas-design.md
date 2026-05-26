---
name: canvas-design
triggers: [create a poster, design this, piece of art, visual design, make art, canvas design, generate a design]
description: Create original visual art as .png or .pdf — posters, abstract compositions, editorial graphics. Two-step workflow: design philosophy then canvas execution. Use when the user wants a designed visual artifact, not a wireframe or UI component.
inject: on-trigger
claude_code_skills: []
source: anthropics/skills
---

# Canvas Design Skill

Two-step workflow: **Design Philosophy** → **Canvas Creation**.

Output: `.md` (philosophy) + `.png` or `.pdf` (final artifact).

---

## Step 1 — Design Philosophy

Create a VISUAL PHILOSOPHY — an aesthetic movement — not a layout or template.

### Name the movement
1–2 words: "Brutalist Joy" / "Chromatic Silence" / "Metabolist Dreams"

### Write the philosophy (4–6 paragraphs)
Address how the aesthetic manifests through:
- Space and form
- Color and material
- Scale and rhythm
- Composition and balance
- Visual hierarchy

**Key requirements:**
- Each design aspect mentioned once — no repetition
- Stress mastery repeatedly: "meticulously crafted," "painstaking attention," "master-level execution," "the product of countless hours"
- Keep generic enough that the next Claude has interpretive room
- Leave creative space — specify direction, not every detail

### Philosophy examples (condensed — actual output should be 4–6 substantial paragraphs)

**"Concrete Poetry"** — communication through monumental form and bold geometry. Massive color blocks, sculptural typography, Brutalist spatial divisions, Polish poster energy meets Le Corbusier. Text as rare, powerful gesture — never paragraphs.

**"Chromatic Language"** — color as the primary information system. Geometric precision where color zones create meaning. Typography minimal — small sans-serif labels. Information encoded spatially and chromatically.

**"Analog Meditation"** — quiet contemplation through texture and breathing room. Paper grain, ink bleeds, vast negative space. Japanese photobook aesthetic. Text whispered.

Save the philosophy as a `.md` file alongside the artifact.

---

## Step 2 — Deduce the Subtle Reference

Before drawing: identify the conceptual thread from the user's request.

The topic is a **subtle, niche reference embedded within the art** — not always literal, always sophisticated. Someone familiar with the subject should feel it intuitively; others simply experience a masterful composition. Think like a jazz musician quoting another song — only those who know will catch it.

---

## Step 3 — Canvas Creation

Generate a `.pdf` or `.png` using Python (reportlab, PIL/Pillow, matplotlib) or an HTML/canvas artifact. One page, highly visual, design-forward.

### Principles
- 90% visual, 10% essential text
- Use repeating patterns and perfect shapes
- Text is minimal — a few words max, integrated as visual element
- Nothing falls off-page; all elements within canvas boundaries with proper margins
- Vary text weight based on context (punk poster → aggressive; minimalist studio → whisper)

### Font guidance
Use Google Fonts via CDN (`https://fonts.googleapis.com/css2?family=...`) for web/HTML artifacts, or system fonts (Helvetica, Georgia, Courier) for Python/PDF outputs. **Different fonts for different text roles.** Make typography part of the art — bring it onto the canvas, not just typeset digitally.

### Craftsmanship requirements
Create work that looks like it took countless hours — someone at the top of their field labored over every detail with painstaking care. Double-check:
- Nothing overlaps, nothing clips
- Flawless composition and spacing
- Color choices are intentional and cohesive
- Typography is design-forward

---

## Step 4 — Final Polish

**CRITICAL**: Before declaring done — refine what exists, don't add more elements.

Ask: "How can I make what's already here more of a piece of art?" Avoid adding new shapes or functions. Instead: tighten composition, strengthen color relationships, improve typographic placement.

---

## Multi-page Option

If multiple pages requested: treat the first as one page in a coffee table book. Each subsequent page is a unique twist on the same philosophy — a different facet, a memory of the original. Bundle as a `.pdf` or multiple `.png` files.

---

## MewVault Context

- Design artifacts → `design-studio/<project>/assets/`
- Philosophy `.md` → `design-studio/<project>/wiki/<movement-name>.md`
- For idea-hub pitch decks, pair with the `pptx` skill for slide decks
- If a Figma file exists (`figma_file_key` in Project_Status.md), check design direction before creating — `greenlit: true` means the direction is locked
