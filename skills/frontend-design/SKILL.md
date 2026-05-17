---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use when building web components, pages, dashboards, React components, HTML/CSS layouts, or when styling any web UI. Avoids generic AI aesthetics.
origin: anthropics
---

# Frontend Design

Build production-grade frontend interfaces with a clear, bold aesthetic direction. No generic "AI slop."

## Before Writing Code: Design Thinking

Commit to a direction before touching code:

1. **Purpose** — what problem does this interface solve? Who uses it?
2. **Tone** — pick a clear aesthetic extreme and commit to it:
   - Brutally minimal / maximalist / retro-futuristic / organic / luxury
   - Editorial / brutalist / art deco / soft pastel / industrial
3. **Differentiation** — what will the user remember?

**Rule:** Bold maximalism and refined minimalism both work. Bland middle-ground does not. Intentionality is everything.

## Aesthetic Guidelines

**Typography:**
- Choose distinctive, characterful fonts — not Arial, Inter, Roboto, or system fonts
- Pair a display font with a refined body font
- Size, weight, and letter-spacing are design decisions, not defaults

**Color:**
- Commit to a cohesive system (CSS variables)
- Dominant colors with sharp accents beat evenly distributed palettes
- Never default to purple gradients on white backgrounds

**Motion:**
- CSS-only for HTML; Motion library for React
- One orchestrated page-load reveal with staggered delays > scattered micro-animations
- Hover states and scroll-triggered effects that surprise

**Layout:**
- Unexpected: asymmetry, overlap, diagonal flow, grid-breaking elements
- Generous negative space OR controlled density — not the default 50/50

**Backgrounds:**
- Gradient meshes, noise textures, geometric patterns, layered transparencies
- Dramatic shadows, decorative borders, grain overlays
- Never solid white/gray defaults

## Implementation

Match complexity to vision:
- Maximalist → elaborate animations, layered effects, rich detail
- Minimalist → precision spacing, typography-led, subtle hover states

```tsx
// Example: React component with distinctive styling
export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-zinc-950 min-h-screen">
      {/* Grain overlay */}
      <div className="absolute inset-0 opacity-20" style={{
        backgroundImage: "url(\"data:image/svg+xml,...\")"
      }} />
      {/* Content with deliberate typography */}
      <h1 className="font-display text-8xl font-black tracking-tighter text-white">
        Distinctive.
      </h1>
    </section>
  )
}
```

## Never

- Purple gradients on white
- Inter/Roboto/Arial/system-ui as primary typeface
- Centered everything with rounded corners everywhere
- Predictable card grids with equal padding
- Designs that look the same as the last AI-generated UI

## After Building

Test in browser. If it looks like something Claude Code always generates — redesign it.
