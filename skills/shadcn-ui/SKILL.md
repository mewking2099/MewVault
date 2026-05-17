---
name: shadcn-ui
description: Add and configure shadcn/ui components with deep project awareness. Use when adding shadcn components, customizing themes, working with CSS variables, or building with the shadcn registry. Auto-detects project config from components.json.
origin: shadcn
---

# shadcn/ui

Add, configure, and compose shadcn/ui components with project-specific accuracy.

## Step 0: Detect Project Config

Before writing any code, read the project's shadcn config:
```bash
cat components.json 2>/dev/null || echo "No components.json found"
npx shadcn info --json 2>/dev/null || npx shadcn@latest info --json
```

Extract:
- **Framework:** Next.js, Vite, Remix, Astro, etc.
- **Tailwind version:** v3 vs v4 (different CSS variable syntax)
- **Component aliases:** `@/components`, `~/components`, etc.
- **Base library:** Radix UI, React Aria, etc.
- **Icon library:** lucide-react, radix-icons, etc.
- **Installed components:** don't re-add what's already there

## Adding Components

```bash
# Search available components
npx shadcn@latest search <query>

# Add specific component
npx shadcn@latest add button
npx shadcn@latest add card dialog form

# View component source before adding
npx shadcn@latest view button
```

## Composing Components

shadcn components are composable primitives. Follow the project's established patterns:

```tsx
// Correct: use installed component path from components.json aliases
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

// Never: import from shadcn npm package directly
// import { Button } from "@shadcn/ui"  ← WRONG
```

## Theming (Tailwind v3)

CSS variables in `globals.css`:
```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  --radius: 0.5rem;
}
.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
}
```

## Theming (Tailwind v4)

```css
@theme {
  --color-background: oklch(1 0 0);
  --color-foreground: oklch(0.145 0 0);
  --color-primary: oklch(0.205 0 0);
  --radius-sm: 0.25rem;
}
```

## Form Pattern

```tsx
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form"

const form = useForm({
  resolver: zodResolver(schema),
  defaultValues: { email: "" }
})
```

## Key Rules

- Always check `components.json` before assuming component paths
- Never import from `@shadcn/ui` npm — components live in your project
- Use `npx shadcn@latest add` not manual file creation
- Check installed components list before re-adding existing ones
- Match Tailwind version to correct CSS variable syntax
