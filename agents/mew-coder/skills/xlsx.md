---
name: xlsx
triggers: [xlsx, spreadsheet, excel, open this spreadsheet, edit the xlsx, create a spreadsheet, csv file, tsv file, tabular data]
description: Create, read, edit, or fix .xlsx/.csv/.tsv files. Use whenever a spreadsheet file is the primary input or output — adding columns, computing formulas, formatting, cleaning data, financial models. Trigger when the user references a spreadsheet file by name or path, even casually.
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
sheet['B10'] = df['Sales'].sum()     # hardcodes 5000

# Right
sheet['B10'] = '=SUM(B2:B9)'        # stays live
```

This applies to all calculations: totals, percentages, ratios, growth rates.

## Financial Model Standards

When building financial models:

### Color Coding (industry standard)
- **Blue text** `(0,0,255)` — hardcoded inputs users change for scenarios
- **Black text** `(0,0,0)` — all formulas and calculations
- **Green text** `(0,128,0)` — links from other sheets in same workbook
- **Red text** `(255,0,0)` — external links to other files
- **Yellow background** `(255,255,0)` — key assumptions needing attention

```python
from openpyxl.styles import Font, PatternFill
sheet['B5'].font = Font(color='0000FF')  # blue input
sheet['C5'].font = Font(color='000000')  # black formula
```

### Number Formatting
- Currency: `$#,##0` — always specify units in headers (`Revenue ($mm)`)
- Zeros: format as `"-"` → use `"$#,##0;($#,##0);-"`
- Percentages: `0.0%`
- Negative numbers: parentheses `(123)` not minus `-123`
- Years: text strings `"2024"` not `2,024`

### Assumptions
Place all assumptions (growth rates, margins, multiples) in dedicated cells. Use cell references, never hardcoded values inside formulas.

Document hardcodes:
```
Source: Company 10-K, FY2024, Page 45, Revenue Note
```

## Recalculation Workflow

```bash
# After creating/editing with openpyxl:
python scripts/recalc.py output.xlsx

# Returns JSON:
# { "status": "success", "total_formulas": 42, "total_errors": 0 }
# If "errors_found": check error_summary for #REF!, #DIV/0!, #VALUE!, #NAME?
```

Fix all errors, recalculate again until `"status": "success"`.

## Library Selection

- **pandas** — data analysis, bulk operations, simple data export
- **openpyxl** — complex formatting, formulas, Excel-specific features
- Use `data_only=True` to read calculated values — **warning**: saving after `data_only=True` replaces formulas with static values permanently

## Common Pitfalls

- openpyxl is 1-indexed: `row=1, column=1` = cell A1 (DataFrame row 5 = Excel row 6)
- Cross-sheet references: `Sheet1!A1` format
- Check `pd.notna()` before using values — NaN in formulas causes errors
- Test sample references before building full model
- Division-by-zero: check denominators before writing formulas

## MewVault Context

- Spreadsheet outputs → `software-projects/<project>/` root or a `data/` subdirectory
- Check `Project_Status.md` for tier before building complex models — MewKing tier requires `plan_approved: true`
- Never commit `.xlsx` files with hardcoded secrets or API keys
- Use `mew secret get KEY_NAME` for any credentials needed in data pipelines
