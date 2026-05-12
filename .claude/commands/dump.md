# Dump

Classify a piece of content and route it to the correct location in mewwiki.

## Arguments

`$ARGUMENTS` is the content to dump. It may be a full sentence, a quote, a URL with context, or raw notes.

## Steps

**1. Classify**

Determine the content type:

| Type | Signals | Destination |
|------|---------|-------------|
| `idea` | "what if", "we should", hypothesis, future feature | `mewwiki/Operations/Ideas/inbox.md` |
| `decision` | "we decided", "going with X", rationale + outcome | `mewwiki/Operations/Decisions/<project>-<slug>.md` |
| `person` | observation about a specific person, contact note | `mewwiki/Operations/People/<Name>.md` |
| `meeting` | notes from a meeting, conversation summary | `mewwiki/Operations/Meetings/_inbox/<slug>.md` |
| `api-note` | API behaviour, endpoint quirk, integration note | current silo's `wiki/<slug>.md` |
| `gotcha` | something that burned time, a non-obvious bug | current silo's `wiki/<slug>.md` |
| `concept` | definition, architecture decision, mental model | current silo's `wiki/<slug>.md` |

**2. Propose routing**

Print in one block:
```
Type:    <type>
Route:   <destination path>
Title:   <proposed title>
Project: <project if relevant, else —>

Content preview:
<first 200 chars of what will be written>

Confirm? [y/n/reclassify]
```

Wait for confirmation before writing anything.

**3. Write**

After confirmation, write the note using the matching Template from `mewwiki/Templates/`. The mewwiki path is in `mewvault/.mewwiki`.

- Add a `[[wikilink]]` back to the source project if one is identified.
- For `idea`: append a new bullet to `Operations/Ideas/inbox.md` under `## Ideas`.
- For `decision`: create a new file using the Decision template.
- For `person`: create or append to `Operations/People/<Name>.md`.
- For `api-note` / `gotcha` / `concept`: create in the current silo's `wiki/`. It will flow to mewwiki on next sync.
- For `meeting`: create in `Operations/Meetings/_inbox/` using Meeting Note template.

**4. Confirm**

Print the path written and note that it will appear in Obsidian after the next sync (or immediately if written directly to mewwiki).
