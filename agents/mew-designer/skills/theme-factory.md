---
name: theme-factory
triggers: [apply a theme, theme this, color scheme, choose colors, style guide, pick a theme, theme factory]
description: Apply consistent professional themes (colors + fonts) to any artifact — slides, docs, HTML pages, reports. Has 10 preset themes or can generate a custom one on request.
inject: on-trigger
claude_code_skills: []
source: anthropics/skills
---

# Skill: Theme Factory

Apply consistent, professional styling to any artifact.

## Usage

1. Show the user the 10 available themes below
2. Ask which to apply
3. Wait for selection
4. Apply the chosen theme's colors and fonts consistently throughout

## Available Themes

| # | Theme | Primary | Secondary | Accent | Header Font | Body Font |
|---|-------|---------|-----------|--------|-------------|-----------|
| 1 | **Ocean Depths** | `#1A3A5C` (deep navy) | `#5B9BD5` (ocean blue) | `#E8F4FD` (pale blue) | Playfair Display | Source Sans Pro |
| 2 | **Sunset Boulevard** | `#E8653A` (warm orange) | `#F4A261` (peach) | `#FFF3E0` (cream) | Raleway | Lato |
| 3 | **Forest Canopy** | `#2D6A4F` (forest green) | `#74C69D` (sage) | `#F0FFF4` (mint cream) | Merriweather | Open Sans |
| 4 | **Modern Minimalist** | `#212121` (near black) | `#757575` (mid grey) | `#F5F5F5` (off white) | Inter | Inter |
| 5 | **Golden Hour** | `#B7791F` (amber) | `#D69E2E` (gold) | `#FFFFF0` (ivory) | Libre Baskerville | Nunito |
| 6 | **Arctic Frost** | `#2B6CB0` (ice blue) | `#90CDF4` (frost) | `#EBF8FF` (snow) | Poppins | Roboto |
| 7 | **Desert Rose** | `#9B2335` (dusty rose) | `#C8A4A4` (blush) | `#FFF5F5` (rose white) | Cormorant Garamond | Karla |
| 8 | **Tech Innovation** | `#6B21A8` (electric purple) | `#A855F7` (violet) | `#F5F3FF` (lavender) | Space Grotesk | DM Sans |
| 9 | **Botanical Garden** | `#276749` (deep green) | `#68D391` (leaf) | `#F0FFF4` (pale mint) | Josefin Sans | Crimson Text |
| 10 | **Midnight Galaxy** | `#1A1A2E` (midnight) | `#16213E` (deep space) | `#533483` (nebula purple) | Orbitron | Exo 2 |

## Applying a theme

After selection, read the theme spec above and apply:
- Background: `<Accent>` for content areas, `<Primary>` for headers/title bars
- Text: `<Primary>` for headings, `<Secondary>` for body, white on dark backgrounds
- Header font for all titles, headers, slide titles
- Body font for all body text, captions, bullets
- Apply consistently across all slides/sections — don't mix themes

## Custom theme

If none of the presets fit, generate a new theme:
1. Ask for: mood/aesthetic (1-2 words), context (tech / creative / formal / warm), any specific color input
2. Design a matching palette (Primary + Secondary + Accent) and font pair
3. Name the theme descriptively
4. Show it to the user for approval
5. Apply after approval

## MewVault context

- For design-studio deliverables: check `Project_Status.md` for `greenlit` — if true, the design direction is locked
- For idea-hub pitch decks: pick a theme that fits the idea's market/audience
- For wiki/docs: Modern Minimalist or Forest Canopy work for most technical content
