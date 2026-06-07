# MewVault — Third-Party Tooling

These tools are **optional but recommended**. MewVault works without them. Install only what you need per silo.

---

## Python linting — mewvault CLI

**Tool:** `ruff` — lint + format + import sort in one command.
**Config:** `pyproject.toml → [tool.ruff]` (already set).

```bash
pip install ruff

ruff check mew/          # lint
ruff check mew/ --fix    # lint + auto-fix
ruff format mew/         # format
```

---

## GDScript linting — game-lab

**Tool:** `gdtoolkit==4.*` — `gdlint` + `gdformat`. Godot 4 compatible.
**Config:** `game-lab/fruit-merge/src/.gdlintrc` (already set).

```bash
pip install "gdtoolkit==4.*"
# or:
pip install -r game-lab/requirements-dev.txt

# Run from inside src/
gdlint *.gd           # lint
gdformat *.gd         # format
```

---

## TypeScript / JavaScript analysis — software-projects

**Tool:** `fallow` — dead code, duplication, complexity hotspots. Native Claude Code MCP support.

```bash
# Run without installing
npx fallow            # dead code + duplication + health in one pass
npx fallow dead-code  # unused files, exports, dependencies
npx fallow dupes      # repeated logic
npx fallow health     # complexity hotspots

# Optional: generate a .fallowrc.json tailored to the project
npx fallow init
```

**Claude Code MCP server** (add to `.claude/settings.json`):
```json
{
  "mcpServers": {
    "fallow": {
      "command": "fallow-mcp"
    }
  }
}
```

Requires `fallow-mcp` on PATH. Install globally if wiring up MCP:
```bash
npm install -g fallow
```

**Example `.fallowrc.json`** for software-projects:
```jsonc
{
  "$schema": "https://raw.githubusercontent.com/fallow-rs/fallow/main/schema.json",
  "entry": ["src/**/*.ts", "app/**/*.tsx"],
  "ignorePatterns": ["**/*.generated.ts", "**/*.d.ts"],
  "rules": {
    "unused-files": "error",
    "unused-exports": "warn",
    "unused-types": "off"
  }
}
```

---

## Knowledge graph — all silos

**Tool:** `graphifyy` (pip) — maps code, docs, PDFs into a queryable knowledge graph. Installs as a Claude Code `/graphify` skill.

```bash
pip install graphifyy
graphify install --project    # run from each silo root to register the skill
```

**Usage in Claude Code:**
```
/graphify .
```
Outputs `graphify-out/graph.html`, `GRAPH_REPORT.md`, `graph.json`.

**Status:** Not yet installed. Run the two commands above.
