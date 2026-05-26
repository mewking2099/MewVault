---
name: browser-use
triggers: [browse this, open this url, read this page, scrape this, follow the links, multi-page research, navigate to, extract from website]
description: Systematic multi-page web research — traverse paginated results, extract structured data, track sources. Use when WebSearch alone isn't enough and you need to read full pages, follow links, or extract data across multiple URLs.
inject: on-trigger
claude_code_skills: []
source: mewvault/custom
---

# Browser Use Skill

Structured multi-page web research using WebFetch + WebSearch. Use when a single search query isn't enough — you need to read full pages, follow links, or traverse paginated results.

> For **interactive browser automation** (click buttons, fill forms, login flows) — use the `webapp-testing` skill with Playwright instead.

## When to use

- Reading a full article or report beyond the search snippet
- Extracting a structured table from a live page (competitors, pricing, job listings)
- Traversing paginated results (ProductHunt, HackerNews, LinkedIn)
- Following a chain of links (company → team → LinkedIn)
- Cross-referencing multiple URLs from a single search

## Core workflow

### Step 1 — Plan the crawl
Before fetching, list:
- Starting URLs (from WebSearch or user-provided)
- Target data to extract
- Max depth (how many link-hops to follow — default 1, max 2)
- Max pages (cap at 10 unless user specifies more)

### Step 2 — Fetch and extract
```
WebFetch(url) → extract target data → identify next URLs if needed → repeat
```

For paginated results, detect URL patterns:
- `?page=N` → increment N
- `?offset=N` → increment by page size
- `?cursor=...` → use next-page cursor from response

Stop when: target data collected, max pages reached, or no next-page signal found.

### Step 3 — Handle JS-rendered pages
WebFetch handles static HTML. When a page returns minimal content (likely JS-rendered):
1. Try fetching with `Accept: text/html` and a real User-Agent via Bash + curl:
   ```bash
   curl -s -A "Mozilla/5.0" -L "<url>" | python3 -m html.parser
   ```
2. If still empty — note it as JS-gated and search for a cached/AMP version or API endpoint instead
3. Never spend more than 2 attempts on a single JS-gated page — move on

### Step 4 — Source tracking
Every extracted fact gets a source citation:
```
(source: <url>, accessed 2026-05-26)
```

Build a source list as you go. Paste into `feasibility.md` or `research/` files at the end.

## Common research patterns

### Competitor pricing page
```
1. WebSearch: "<competitor> pricing"
2. WebFetch: pricing page URL
3. Extract: plan names, prices, feature limits
4. Repeat for 3-5 competitors
5. Build comparison table
```

### ProductHunt launch history
```
1. WebFetch: https://www.producthunt.com/search?q=<topic>
2. Extract: product names, upvotes, launch dates, taglines
3. Follow top 3-5 product URLs for detail
```

### Market size signal
```
1. WebSearch: "<market> market size 2024 OR 2025"
2. WebFetch: top 2-3 results (industry reports, Statista, McKinsey)
3. Extract: TAM numbers, CAGR, source year
4. Note: prefer primary sources (analyst reports) over blog aggregators
```

## Output format

After traversal, produce a structured extract:
```markdown
## Research: <topic>

**Sources visited**: N pages
**Date**: YYYY-MM-DD

### Extracted data
[table or bullet list]

### Source list
- [Title](url) — accessed YYYY-MM-DD
- [Title](url) — accessed YYYY-MM-DD
```

## MewVault context

- Drop raw extracts into `idea-hub/ideas/<slug>/research/` — immutable once saved
- Processed/synthesised data goes in `feasibility.md` or `wiki/` pages
- Cite every number: `(source: research/<filename>.md)`
- If a page blocks WebFetch: note it in the source list as `[blocked — JS-gated or paywalled]`
