---
name: edit-docs
description: Pull a Google Doc's state and edit it.
---

I use Google Docs to keep a lot of running notes about my life.

**Note**: For questions about the Google Docs API, use the deepwiki MCP on the `googleapis/google-api-python-client` repo.
**CLI input contract**: Pass `--doc-id <DOC_ID>` on every command. The CLI expects a raw Google Docs document ID (agents can extract it from a docs URL before calling).

## Listing tabs

```bash
uv run python projects/docs-cli/google_docs.py --doc-id "<DOC_ID>" tabs
```

Shows all tabs with their titles and IDs, including nested tabs.

## Deleting a tab

```bash
uv run python projects/docs-cli/google_docs.py --doc-id "<DOC_ID>" delete-tab "Tab Name"    # by title
uv run python projects/docs-cli/google_docs.py --doc-id "<DOC_ID>" delete-tab "t.abc123"    # by ID
```

Deletes a tab and all its child tabs.

## Reading a tab

```bash
uv run python projects/docs-cli/google_docs.py --doc-id "<DOC_ID>" get                    # first tab
uv run python projects/docs-cli/google_docs.py --doc-id "<DOC_ID>" get --tab "Food"       # by title
uv run python projects/docs-cli/google_docs.py --doc-id "<DOC_ID>" get --tab "t.abc123"   # by ID
```

Output is a compact indexed format. Each line starts with `[N]` where N is the character index.

**Tables** are displayed with `<|TABLE|>`, **images** with `<|IMAGE|>` or `<|IMAGE uri=...|>`, and **links** with `<|LINK url=...|>text<|/LINK|>`:

```
[1] # Weekly Goals
[16] - Finish the API integration
[90]
[91] <|TABLE|>
  Row 1: | Column A | Column B |
  Row 2: | Data 1 | Data 2 |
[150] Check out <|LINK url=https://example.com|>this page<|/LINK|>
[200] <|IMAGE uri=https://lh7-us.googleusercontent.com/...|>
```

## Editing a tab

All update commands accept `--tab` to target a specific tab (default: first tab).

| Command | Description |
|---|---|
| `update replace "old" "new"` | Case-sensitive literal find/replace all occurrences |
| `update replace -E "pattern" "replacement"` | Regex find/replace (supports `\1`, `\2` backrefs) |
| `update append "new text"` | Add text to the end of the tab |
| `update insert <index> "text"` | Insert text at a specific character index |
| `update delete <start> <end>` | Delete the character range [start, end) |
| `update link <start> <end> "url"` | Add a hyperlink to text in range [start, end) |
| `update link <start> <end>` | Remove a hyperlink from text in range |
| `update insert-table-row <table_index> <row>` | Insert row below row N in table at index |
| `update insert-table-row <table_index> <row> --above` | Insert row above row N |
| `update delete-table-row <table_index> <row>` | Delete row N from table at index |

All commands accept `--tab` (e.g. `uv run python projects/docs-cli/google_docs.py --doc-id "<DOC_ID>" update --tab "Food" append "text"`). Without `--tab`, `replace` operates on **all tabs**; other commands default to the first tab.

**Note**: `insert`/`delete` work inside table cells too — use the character index shown in `get` output. The `table_index` for table row commands is the index shown on the `<|TABLE|>` line.

## Workflow guidance

- **Prefer `replace`** for edits — it doesn't depend on indices and is the safest editing command.
  - Literal mode: `update replace "old text" "new text"` — exact match, case-sensitive.
  - Regex mode: `update replace -E "(\w+)@(\w+)" "\1 at \2"` — full Python regex with backreferences.
  - Regex mode works inside tables too.
- **Use `append`** for most new content — it handles finding the end of the tab automatically.
- **Run `tabs` first** to see available tabs if you're unsure of the name.
- **Always `get` first** before making edits so you have current indices.
- **Re-`get` after positional edits** (`insert`/`delete`) since indices shift.
- **Edit bottom-to-top** if making multiple index-based edits in one session, so earlier indices stay valid.
