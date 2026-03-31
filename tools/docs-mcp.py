from __future__ import annotations

import os
import re
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP  # type: ignore

mcp = FastMCP("docs-mcp")

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/tasks",
]


def _token_path() -> str:
    return os.environ.get("GOOGLE_DOCS_TOKEN_PATH", "token.json")


def _credentials_path() -> str:
    return os.environ.get("GOOGLE_DOCS_CREDENTIALS_PATH", "credentials.json")


def _auth_guidance() -> str:
    token_path = _token_path()
    creds_path = _credentials_path()
    return (
        "copy valid OAuth files into the sprite and re-run: "
        f"token='{token_path}', credentials='{creds_path}'. "
        "Generate token.json by running google_docs.py locally once and completing login."
    )


def _get_service():
    token_path = _token_path()
    if not os.path.exists(token_path):
        raise RuntimeError(f"missing token file '{token_path}'; {_auth_guidance()}")

    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    except Exception as err:
        raise RuntimeError(f"could not parse token file '{token_path}': {err}") from err

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as err:
                raise RuntimeError(f"token refresh failed: {err}; {_auth_guidance()}") from err
            with open(token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
        else:
            raise RuntimeError(f"token is invalid and not refreshable; {_auth_guidance()}")

    return build("docs", "v1", credentials=creds)


def _get_doc(service, doc_id: str) -> dict[str, Any]:
    return (
        service.documents()
        .get(documentId=doc_id, includeTabsContent=True)
        .execute()
    )


def _batch_update_doc(service, doc_id: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
    return service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests},
    ).execute()


def _flatten_tabs(tabs: list[dict[str, Any]], depth: int = 0) -> list[tuple[dict[str, Any], int]]:
    result: list[tuple[dict[str, Any], int]] = []
    for tab in tabs:
        result.append((tab, depth))
        result.extend(_flatten_tabs(tab.get("childTabs", []), depth + 1))
    return result


def _available_tabs_message(doc: dict[str, Any]) -> str:
    all_tabs = _flatten_tabs(doc.get("tabs", []))
    if not all_tabs:
        return "Available tabs: none"

    lines = ["Available tabs:"]
    for tab, depth in all_tabs:
        props = tab.get("tabProperties", {})
        indent = "  " * depth
        lines.append(f"  {indent}{props.get('title', '(untitled)')} [{props.get('tabId')}]")
    return "\n".join(lines)


def _find_tab(doc: dict[str, Any], tab_query: str | None) -> dict[str, Any] | None:
    all_tabs = _flatten_tabs(doc.get("tabs", []))
    if not tab_query:
        if all_tabs:
            return all_tabs[0][0]
        return None

    for tab, _ in all_tabs:
        props = tab.get("tabProperties", {})
        if props.get("title") == tab_query or props.get("tabId") == tab_query:
            return tab

    raise ValueError(f"tab not found: {tab_query}\n{_available_tabs_message(doc)}")


def _require_tab(doc: dict[str, Any], tab_query: str | None) -> dict[str, Any]:
    tab = _find_tab(doc, tab_query)
    if tab is None:
        raise ValueError("document has no tabs")
    return tab


def _extract_raw_text(body: dict[str, Any]) -> list[tuple[int, str]]:
    chars: list[tuple[int, str]] = []
    for element in body.get("content", []):
        paragraph = element.get("paragraph")
        if paragraph:
            for run in paragraph.get("elements", []):
                text_run = run.get("textRun")
                if text_run:
                    start = run.get("startIndex", 0)
                    for i, char in enumerate(text_run.get("content", "")):
                        chars.append((start + i, char))

        table = element.get("table")
        if table:
            for row in table.get("tableRows", []):
                for cell in row.get("tableCells", []):
                    for cell_element in cell.get("content", []):
                        paragraph = cell_element.get("paragraph")
                        if not paragraph:
                            continue
                        for run in paragraph.get("elements", []):
                            text_run = run.get("textRun")
                            if text_run:
                                start = run.get("startIndex", 0)
                                for i, char in enumerate(text_run.get("content", "")):
                                    chars.append((start + i, char))

    chars.sort(key=lambda item: item[0])
    return chars


def _extract_paragraph_text(
    paragraph: dict[str, Any],
    inline_objects: dict[str, Any] | None = None,
) -> str:
    text = ""
    for run in paragraph.get("elements", []):
        text_run = run.get("textRun")
        if text_run:
            content = text_run.get("content", "")
            link = text_run.get("textStyle", {}).get("link", {})
            url = link.get("url", "")
            if url and content.strip():
                text += f"<|LINK url={url}|>{content.rstrip(chr(10))}<|/LINK|>"
            else:
                text += content

        inline_obj = run.get("inlineObjectElement")
        if inline_obj and inline_objects:
            obj_id = inline_obj.get("inlineObjectId", "")
            obj = inline_objects.get(obj_id, {})
            embedded = obj.get("inlineObjectProperties", {}).get("embeddedObject", {})
            uri = embedded.get("imageProperties", {}).get("contentUri", "")
            if uri:
                text += f"<|IMAGE uri={uri}|>"
            else:
                text += "<|IMAGE|>"
        elif inline_obj:
            text += "<|IMAGE|>"

    return text.rstrip("\n")


def _format_table(
    table_element: dict[str, Any],
    start_index: int,
    inline_objects: dict[str, Any] | None = None,
) -> str:
    lines = [f"[{start_index}] <|TABLE|>"]
    table = table_element.get("table", {})
    rows = table.get("tableRows", [])

    for row_idx, row in enumerate(rows):
        cells = row.get("tableCells", [])
        row_text: list[str] = []
        for cell in cells:
            cell_content: list[str] = []
            for content_element in cell.get("content", []):
                paragraph = content_element.get("paragraph")
                if paragraph:
                    text = _extract_paragraph_text(paragraph, inline_objects)
                    if text:
                        cell_content.append(text)
            row_text.append(" ".join(cell_content) if cell_content else "")

        lines.append(f"  Row {row_idx + 1}: | {' | '.join(row_text)} |")

    return "\n".join(lines)


def _format_tab_body(body: dict[str, Any], inline_objects: dict[str, Any] | None = None) -> str:
    lines: list[str] = []
    heading_map = {
        "HEADING_1": "# ",
        "HEADING_2": "## ",
        "HEADING_3": "### ",
        "HEADING_4": "#### ",
        "HEADING_5": "##### ",
        "HEADING_6": "###### ",
    }

    for element in body.get("content", []):
        start_index = element.get("startIndex", 0)

        if "table" in element:
            lines.append(_format_table(element, start_index, inline_objects))
            continue

        paragraph = element.get("paragraph")
        if not paragraph:
            continue

        style = paragraph.get("paragraphStyle", {})
        named_style = style.get("namedStyleType", "NORMAL_TEXT")
        bullet = paragraph.get("bullet")

        text = _extract_paragraph_text(paragraph, inline_objects)

        prefix = ""
        if named_style in heading_map:
            prefix = heading_map[named_style]
        elif bullet:
            nesting = bullet.get("nestingLevel", 0)
            prefix = "  " * nesting + "- "

        lines.append(f"[{start_index}] {prefix}{text}")

    return "\n".join(lines)


def _tool_result(action):
    try:
        return action()
    except HttpError as err:
        return f"API error: {err}"
    except Exception as err:
        return f"error: {err}"


@mcp.tool()
def docs_tabs(doc_id: str) -> str:
    """List all tabs for a Google Doc.

    Args:
        doc_id: Raw Google Docs document ID.
    """

    def action() -> str:
        service = _get_service()
        doc = _get_doc(service, doc_id)
        lines: list[str] = []
        title = doc.get("title", "")
        if title:
            lines.append(f"# {title}")
            lines.append("")
        all_tabs = _flatten_tabs(doc.get("tabs", []))
        for tab, depth in all_tabs:
            props = tab.get("tabProperties", {})
            indent = "  " * depth
            lines.append(f"{indent}{props.get('title', '(untitled)')}  [{props.get('tabId')}]")
        if not all_tabs:
            lines.append("(no tabs)")
        return "\n".join(lines).rstrip()

    return _tool_result(action)


@mcp.tool()
def docs_get(doc_id: str, tab: str = "") -> str:
    """Get one tab from a Google Doc in indexed plain-text form.

    Args:
        doc_id: Raw Google Docs document ID.
        tab: Tab title or tab ID. Defaults to the first tab.
    """

    def action() -> str:
        service = _get_service()
        doc = _get_doc(service, doc_id)
        target_tab = _require_tab(doc, tab or None)
        props = target_tab.get("tabProperties", {})
        doc_tab = target_tab.get("documentTab", {})
        body = doc_tab.get("body", {})
        inline_objects = doc_tab.get("inlineObjects", {})
        header = f"# {doc.get('title', '')} > {props.get('title', '(untitled)')}"
        return f"{header}\n\n{_format_tab_body(body, inline_objects)}".rstrip()

    return _tool_result(action)


@mcp.tool()
def docs_append(doc_id: str, text: str, tab: str = "") -> str:
    """Append text to the end of a tab.

    Args:
        doc_id: Raw Google Docs document ID.
        text: Text to append.
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = _get_service()
        doc = _get_doc(service, doc_id)
        target_tab = _require_tab(doc, tab or None)
        props = target_tab.get("tabProperties", {})
        tab_id = props.get("tabId")

        body = target_tab.get("documentTab", {}).get("body", {})
        body_content = body.get("content", [])
        if not body_content:
            raise ValueError("tab body is empty; could not determine append position")
        end_index = body_content[-1]["endIndex"] - 1

        new_text = text if text.startswith("\n") else "\n" + text
        requests = [{"insertText": {"location": {"index": end_index, "tabId": tab_id}, "text": new_text}}]
        _batch_update_doc(service, doc_id, requests)
        return f"Appended text at index {end_index} in tab '{props.get('title')}'"

    return _tool_result(action)


def _replace_literal(service, doc: dict[str, Any], doc_id: str, old: str, new: str, tab: str) -> str:
    tab_id = None
    tab_title = "all tabs"
    if tab:
        target_tab = _require_tab(doc, tab)
        props = target_tab.get("tabProperties", {})
        tab_id = props.get("tabId")
        tab_title = f"tab '{props.get('title')}'"

    request: dict[str, Any] = {
        "replaceAllText": {
            "containsText": {"text": old, "matchCase": True},
            "replaceText": new,
        }
    }
    if tab_id:
        request["replaceAllText"]["tabsCriteria"] = {"tabIds": [tab_id]}

    result = _batch_update_doc(service, doc_id, [request])
    count = (
        result.get("replies", [{}])[0]
        .get("replaceAllText", {})
        .get("occurrencesChanged", 0)
    )
    return f"Replaced {count} occurrence(s) in {tab_title}"


def _replace_regex(service, doc: dict[str, Any], doc_id: str, pattern_text: str, repl: str, tab: str) -> str:
    pattern = re.compile(pattern_text)
    if tab:
        tabs_to_search = [_require_tab(doc, tab)]
    else:
        tabs_to_search = [item for item, _ in _flatten_tabs(doc.get("tabs", []))]

    total = 0
    lines: list[str] = []
    for current_tab in tabs_to_search:
        props = current_tab.get("tabProperties", {})
        tab_id = props.get("tabId")
        body = current_tab.get("documentTab", {}).get("body", {})
        chars = _extract_raw_text(body)
        if not chars:
            continue

        text = "".join(char for _, char in chars)
        doc_indices = [idx for idx, _ in chars]
        matches = list(pattern.finditer(text))
        if not matches:
            continue

        requests: list[dict[str, Any]] = []
        for match in reversed(matches):
            replacement = match.expand(repl)
            start_doc = doc_indices[match.start()]
            end_doc = doc_indices[match.end() - 1] + 1
            requests.append(
                {
                    "deleteContentRange": {
                        "range": {
                            "startIndex": start_doc,
                            "endIndex": end_doc,
                            "tabId": tab_id,
                        }
                    }
                }
            )
            if replacement:
                requests.append(
                    {
                        "insertText": {
                            "location": {"index": start_doc, "tabId": tab_id},
                            "text": replacement,
                        }
                    }
                )

        _batch_update_doc(service, doc_id, requests)
        total += len(matches)
        lines.append(f"Replaced {len(matches)} match(es) in tab '{props.get('title')}'")

    if total == 0:
        return "No matches found"
    return "\n".join(lines)


@mcp.tool()
def docs_replace(
    doc_id: str,
    old: str,
    new: str,
    regex: bool = False,
    tab: str = "",
) -> str:
    """Find and replace text.

    Args:
        doc_id: Raw Google Docs document ID.
        old: Search text (literal or regex pattern).
        new: Replacement text.
        regex: When true, treat 'old' as a regex pattern.
        tab: Optional tab title/ID. With regex=false and no tab, replaces across all tabs.
    """

    def action() -> str:
        service = _get_service()
        doc = _get_doc(service, doc_id)
        if regex:
            return _replace_regex(service, doc, doc_id, old, new, tab)
        return _replace_literal(service, doc, doc_id, old, new, tab)

    return _tool_result(action)


@mcp.tool()
def docs_insert(doc_id: str, index: int, text: str, tab: str = "") -> str:
    """Insert text at a specific index.

    Args:
        doc_id: Raw Google Docs document ID.
        index: Character index to insert at.
        text: Text to insert.
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = _get_service()
        doc = _get_doc(service, doc_id)
        target_tab = _require_tab(doc, tab or None)
        props = target_tab.get("tabProperties", {})
        tab_id = props.get("tabId")
        requests = [{"insertText": {"location": {"index": index, "tabId": tab_id}, "text": text}}]
        _batch_update_doc(service, doc_id, requests)
        return f"Inserted text at index {index} in tab '{props.get('title')}'"

    return _tool_result(action)


@mcp.tool()
def docs_delete(doc_id: str, start_index: int, end_index: int, tab: str = "") -> str:
    """Delete a text range [start_index, end_index).

    Args:
        doc_id: Raw Google Docs document ID.
        start_index: Start index (inclusive).
        end_index: End index (exclusive).
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = _get_service()
        doc = _get_doc(service, doc_id)
        target_tab = _require_tab(doc, tab or None)
        props = target_tab.get("tabProperties", {})
        tab_id = props.get("tabId")
        requests = [
            {
                "deleteContentRange": {
                    "range": {
                        "startIndex": start_index,
                        "endIndex": end_index,
                        "tabId": tab_id,
                    }
                }
            }
        ]
        _batch_update_doc(service, doc_id, requests)
        return f"Deleted range [{start_index}, {end_index}) in tab '{props.get('title')}'"

    return _tool_result(action)


@mcp.tool()
def docs_link(doc_id: str, start_index: int, end_index: int, url: str = "", tab: str = "") -> str:
    """Add or remove a hyperlink on a range.

    Args:
        doc_id: Raw Google Docs document ID.
        start_index: Start index (inclusive).
        end_index: End index (exclusive).
        url: URL to set. Empty string removes the link.
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = _get_service()
        doc = _get_doc(service, doc_id)
        target_tab = _require_tab(doc, tab or None)
        props = target_tab.get("tabProperties", {})
        tab_id = props.get("tabId")

        text_style = {"link": {"url": url}} if url else {}
        requests = [
            {
                "updateTextStyle": {
                    "range": {
                        "startIndex": start_index,
                        "endIndex": end_index,
                        "tabId": tab_id,
                    },
                    "textStyle": text_style,
                    "fields": "link",
                }
            }
        ]
        _batch_update_doc(service, doc_id, requests)
        if url:
            return (
                f"Linked [{start_index}, {end_index}) to {url} "
                f"in tab '{props.get('title')}'"
            )
        return (
            f"Removed link from [{start_index}, {end_index}) "
            f"in tab '{props.get('title')}'"
        )

    return _tool_result(action)


@mcp.tool()
def docs_insert_table_row(
    doc_id: str,
    table_index: int,
    row: int,
    below: bool = True,
    tab: str = "",
) -> str:
    """Insert a row in a table.

    Args:
        doc_id: Raw Google Docs document ID.
        table_index: Start index of the target table element.
        row: Row index (0-based) to insert relative to.
        below: Insert below when true, above when false.
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = _get_service()
        doc = _get_doc(service, doc_id)
        target_tab = _require_tab(doc, tab or None)
        props = target_tab.get("tabProperties", {})
        tab_id = props.get("tabId")

        requests = [
            {
                "insertTableRow": {
                    "tableCellLocation": {
                        "tableStartLocation": {"index": table_index, "tabId": tab_id},
                        "rowIndex": row,
                        "columnIndex": 0,
                    },
                    "insertBelow": below,
                }
            }
        ]
        _batch_update_doc(service, doc_id, requests)
        direction = "below" if below else "above"
        return (
            f"Inserted row {direction} row {row} in table at index {table_index} "
            f"in tab '{props.get('title')}'"
        )

    return _tool_result(action)


@mcp.tool()
def docs_delete_table_row(doc_id: str, table_index: int, row: int, tab: str = "") -> str:
    """Delete a table row.

    Args:
        doc_id: Raw Google Docs document ID.
        table_index: Start index of the target table element.
        row: Row index (0-based) to delete.
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = _get_service()
        doc = _get_doc(service, doc_id)
        target_tab = _require_tab(doc, tab or None)
        props = target_tab.get("tabProperties", {})
        tab_id = props.get("tabId")

        requests = [
            {
                "deleteTableRow": {
                    "tableCellLocation": {
                        "tableStartLocation": {"index": table_index, "tabId": tab_id},
                        "rowIndex": row,
                        "columnIndex": 0,
                    }
                }
            }
        ]
        _batch_update_doc(service, doc_id, requests)
        return (
            f"Deleted row {row} from table at index {table_index} "
            f"in tab '{props.get('title')}'"
        )

    return _tool_result(action)


@mcp.tool()
def docs_delete_tab(doc_id: str, tab: str) -> str:
    """Delete a tab by title or ID.

    Args:
        doc_id: Raw Google Docs document ID.
        tab: Tab title or tab ID.
    """

    def action() -> str:
        service = _get_service()
        doc = _get_doc(service, doc_id)
        target_tab = _require_tab(doc, tab)
        props = target_tab.get("tabProperties", {})
        tab_id = props.get("tabId")
        tab_title = props.get("title", "(untitled)")
        requests = [{"deleteTab": {"tabId": tab_id}}]
        _batch_update_doc(service, doc_id, requests)
        return f"Deleted tab '{tab_title}' [{tab_id}]"

    return _tool_result(action)


if __name__ == "__main__":
    mcp.run(transport="stdio")
