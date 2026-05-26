---
name: xlsx
triggers: [xlsx, spreadsheet, excel, open this spreadsheet, edit the xlsx, create a spreadsheet, csv file, tsv file, tabular data, build a model, market data table]
description: Create, read, edit, or fix .xlsx/.csv/.tsv files. Use whenever a spreadsheet file is the primary input or output — market sizing tables, competitor comparison grids, feasibility data, research exports. Trigger when the user references a spreadsheet file by name or path, even casually.
inject: on-trigger
claude_code_skills: []
source: anthropics/skills
---

# XLSX Skill

## Quick Reference

| Task | Tool |
|------|------|
| Read / analyse data | `pandas` |
| Create / edit with formulas + formatting | `openpyxl` |
| Recalculate formulas after edit | `scripts/recalc.py` (see note below) |

> **Scripts note**: `scripts/recalc.py` requires LibreOffice and is part of the Anthropic skills scripts package. Install via `/plugin install example-skills@anthropic-agent-skills` or from `https://github.com/anthropics/skills`. Without it, formulas are stored as strings — use LibreOffice or Excel to open the file to trigger recalculation.

## Reading and Analysing

```python
import pandas as pd

df = pd.read_excel('file.xlsx')           # first sheet
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # all sheets as dict
df.head(); df.info(); df.describe()

df.to_excel('output.xlsx', index=False)
```

## Creating / Editing (openpyxl)

```python
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

# Create
wb = Workbook()
sheet = wb.active
sheet['A1'] = 'Label'
sheet['B2'] = '=SUM(A1:A10)'   # Always use Excel formulas, not Python-computed values
sheet['A1'].font = Font(bold=True, color='FF0000')
sheet.column_dimensions['A'].width = 20
wb.save('output.xlsx')

# Edit existing
wb = load_workbook('existing.xlsx')
sheet = wb['SheetName']
sheet['A1'] = 'New Value'
wb.save('modified.xlsx')
```

## CRITICAL: Use Formulas, Not Hardcoded Values

Always let Excel calculate — the spreadsheet must remain dynamic:

```python
# Wrong
sheet['B10'] = df['Revenue'].sum()   # hardcodes a number

# Right
sheet['B10'] = '=SUM(B2:B9)'        # stays live
```

## Recalculation Workflow

```bash
python scripts/recalc.py output.xlsx
# Returns JSON — check for #REF!, #DIV/0!, #VALUE!, #NAME? errors
# Fix all errors, recalculate again until "status": "success"
```

## Common Research Table Patterns

### Competitor comparison grid
```python
headers = ['Company', 'Founded', 'Funding', 'Users', 'Price', 'Gap']
sheet.append(headers)
for row in competitors:
    sheet.append(row)
```

### Market sizing model
```python
sheet['B2'] = '=B3*B4'   # TAM = addressable units × revenue per unit
sheet['B3'] = 500000     # hardcoded input → blue font
sheet['B4'] = 120        # hardcoded input → blue font
sheet['B3'].font = Font(color='0000FF')
sheet['B4'].font = Font(color='0000FF')
```

### Color coding for research inputs
- **Blue text** `(0,0,255)` — numbers sourced from external data (market reports, company filings)
- **Black text** `(0,0,0)` — calculated values
- **Yellow background** `(255,255,0)` — cells needing verification or source citation

## Source Citations

Every hardcoded number in a research spreadsheet needs a source:
```
Source: Statista, 2024, Global SaaS Market Report, [URL]
Source: Company 10-K, FY2024, Page 45
```

Add as a cell comment or in an adjacent column.

## Library Selection

- **pandas** — data analysis, bulk operations, importing/cleaning raw research data
- **openpyxl** — formatted tables, formulas, Excel-specific features
- Use `data_only=True` to read calculated values — **warning**: saving after `data_only=True` replaces formulas with static values permanently

## MewVault Context

- Research spreadsheets → `idea-hub/ideas/<slug>/` (next to feasibility.md) or `idea-hub/ideas/<slug>/research/` if it's a raw data drop
- `research/` is **immutable** once a file is dropped — do not edit files there; create a new processed version in the parent slug folder
- Feasibility model outputs feed into `feasibility.md` — export key numbers, then cite them inline with `(source: <filename>.xlsx)`
- Never put raw research data directly into feasibility.md — keep it in the spreadsheet and cite it
