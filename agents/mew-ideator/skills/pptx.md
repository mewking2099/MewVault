---
name: pptx
triggers: [pitch deck, slide deck, presentation, slides, pptx, make slides, create a deck]
description: Create, edit, or extract content from .pptx presentations. Use whenever the user mentions deck, slides, presentation, or a .pptx file — even if pptx isn't the final goal. For idea-hub, this produces pitch decks from idea briefs.
inject: on-trigger
claude_code_skills: []
source: anthropics/skills
---

# PPTX Skill

> **Scripts note**: Full script support (thumbnail.py, soffice.py, visual QA) requires installing the Anthropic skills scripts from https://github.com/anthropics/skills or via `/plugin install example-skills@anthropic-agent-skills`. The workflows below use markitdown and pptxgenjs which are available via pip/npm.

## Quick Reference

| Task | Method |
|------|--------|
| Read/analyse content | `python -m markitdown presentation.pptx` |
| Create from scratch | Use pptxgenjs (see below) |
| Dependencies | `pip install "markitdown[pptx]"` · `npm install -g pptxgenjs` |

## Reading Content

```bash
python -m markitdown presentation.pptx
```

## Creating from Scratch (pptxgenjs)

Use when building a pitch deck from an idea brief or creating a new presentation.

```javascript
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();

// Slide 1 — Title
let slide = pres.addSlide();
slide.addText("Idea Title", {
  x: 0.5, y: 1.5, w: "90%", h: 1.5,
  fontSize: 44, bold: true, color: "1A3A5C", align: "center"
});
slide.addText("One-sentence tagline", {
  x: 0.5, y: 3.2, w: "90%",
  fontSize: 20, color: "5B9BD5", align: "center"
});

// Slide 2 — The Problem
slide = pres.addSlide();
slide.addText("The Problem", { x: 0.5, y: 0.3, fontSize: 28, bold: true, color: "1A3A5C" });
slide.addText("Who has it. What it costs them.", { x: 0.5, y: 1.2, w: "90%", fontSize: 18 });

pres.writeFile({ fileName: "pitch.pptx" });
```

## Design Principles

**Don't create boring slides.** Plain bullets on white are forgettable.

### Before starting
- Pick a bold, content-informed color palette (use theme-factory skill for options)
- Dominant color at 60-70% visual weight, 1-2 supporting tones, one sharp accent
- Commit to ONE visual motif and repeat it across all slides

### Every slide needs a visual element
Layout options:
- Two-column (text left, visual right)
- Icon + text rows (icon in colored circle, bold header, description)
- Large stat callout (60-72pt number, small label below)
- Timeline or process flow

### Typography
| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt |

### Avoid
- Same layout on every slide — vary columns, cards, callouts
- Centre-aligned body text — left-align everything except titles
- Text-only slides — add images, icons, charts, or shapes
- Accent lines under titles — use whitespace or background colour instead

## Pitch Deck Structure (from idea brief)

When building from an `idea-hub/ideas/<slug>/brief.md`:

1. **Title slide** — name + tagline
2. **The Problem** — who has it, what it costs them (2-3 bullets max)
3. **The Solution** — what this makes possible (1 visual + short text)
4. **Target User** — specific person, not a demographic
5. **Why This / Why Now** — differentiator + timing
6. **Market** — size signal + competitor gap (from feasibility.md if available)
7. **How It Works** — 3-step flow or simple diagram
8. **Biggest Risk** — and mitigation (shows you've thought it through)
9. **Next Steps** — what you're doing next, what you need

## QA

Always check for leftover placeholder text:
```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|placeholder"
```

Fix any results before declaring success.

## MewVault context

- Pitch decks go in `idea-hub/ideas/<slug>/` as `pitch.pptx`
- Use `idea-brief.md` as the source content — read it before building slides
- For design-studio pitch deliverables, align with Figma specs first
