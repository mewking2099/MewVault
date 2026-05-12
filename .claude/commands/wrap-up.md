# Wrap Up

End the session cleanly: write the log entry, sync mewwiki, suggest a commit.

## Steps

**1. Detect active project**

Look at the current working directory to determine the active silo project. If ambiguous, ask.

**2. Gather session summary**

If `$ARGUMENTS` is non-empty, use it as the summary text. Otherwise ask:
"What happened this session? (one sentence to a few bullet points)"

**3. Write log entry**

Append to the project's `log.md` (newest on top, under `## Entries`):
```
- **<today YYYY-MM-DD>** — <summary> [auto-wrap]
```

Update `Project_Status.md`:
- `last_session: <today>`
- `last_wrap: <today>`
- `next_action: <ask the user if not obvious>`

**4. Check for orphaned notes**

Scan `mewwiki/_inbox/` for files older than today that have not been routed.
If any exist, list them: "These inbox items are unrouted — review in Obsidian before closing."

**5. Run mew wiki sync**

```bash
python mew.py wiki sync
```

Report what synced.

**6. Suggest commit message**

Based on the session summary, suggest a git commit message in the format:
```
<type>: <summary in imperative mood>

<optional detail line if needed>
```

Where type is: `feat`, `fix`, `refactor`, `docs`, `chore`, or `wip`.

Write the suggestion to `mewvault/.claude/last-session-message.txt` as well.

**7. Print session close**

```
Session wrapped.
Log: <project>/log.md ✓
Wiki sync: <N> project(s) updated ✓
Commit suggestion: <message>

Run: git add ... && git commit -m "<message>"
Or:  mew sync --commit "<message>" --push
```
