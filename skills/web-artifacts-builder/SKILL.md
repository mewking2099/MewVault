---
name: web-artifacts-builder
description: Build elaborate multi-component React artifacts using React 18 + TypeScript + Tailwind CSS + shadcn/ui. Use for complex artifacts requiring state management, routing, or multiple components — not for simple single-file HTML.
origin: anthropics
---

# Web Artifacts Builder

Build powerful multi-component artifacts bundled into a single HTML file.

**Stack:** React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui

**Use this when:** The artifact needs state management, routing, multiple components, or shadcn/ui — not for simple static HTML.

**Use `frontend-design` instead when:** Building a full web page or app (not an artifact), or when you need maximum design freedom.

## When NOT to Use

- Simple static HTML that doesn't need React → just write HTML directly
- Needs a backend → this is frontend artifacts only
- Needs file system access → Artifacts are sandboxed

## Design Guidelines

Avoid generic AI aesthetics:
- No centered purple-gradient layouts
- No Inter as primary font everywhere
- No uniform rounded corners on everything
- Choose a distinctive, intentional visual direction

## Build Process

### 1. Plan the component tree

Before writing code, map out:
```
App
├── Header (navigation, branding)
├── MainContent
│   ├── FeatureSection
│   └── DataDisplay
└── Footer
```

### 2. Initialize with shadcn/ui components

Identify which shadcn components you need:
```bash
# In a real project setup:
npx shadcn@latest add button card dialog tabs
```

For artifacts, include the component code inline or via CDN-equivalent patterns.

### 3. State management pattern

```tsx
// Co-locate state with the component that owns it
// Lift state only when two sibling components need it

const [activeTab, setActiveTab] = useState<"overview" | "detail">("overview")

// For complex state, use useReducer
const [state, dispatch] = useReducer(reducer, initialState)
```

### 4. Bundle into single HTML

All code, styles, and components must compile into one self-contained HTML file. Use Vite or equivalent bundler configured for single-file output.

### 5. Test the artifact

After building:
- Open in browser, verify interactive elements work
- Check for console errors
- Test on narrow viewport (mobile) if responsive design is required
- Verify all state transitions work correctly

## Common Patterns

### Tabs
```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
```

### Data table with sorting
```tsx
// Use TanStack Table (react-table) for complex tables
// Use simple array.sort() for basic cases
```

### Modal/Dialog
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
const [open, setOpen] = useState(false)
```

## After Building

Run `webapp-testing` skill to verify behavior with Playwright if the artifact is complex.
