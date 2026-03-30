"""MCP server for Google Tasks API v1 (REST).

Auth: set GOOGLE_TASKS_CLIENT_ID, GOOGLE_TASKS_CLIENT_SECRET, and
GOOGLE_TASKS_REFRESH_TOKEN (from a one-time OAuth flow with scope
https://www.googleapis.com/auth/tasks).

Alternatively, GOOGLE_TASKS_CREDENTIALS_JSON may point to a JSON file with keys
client_id, client_secret, refresh_token (and optional token_uri).
"""

from __future__ import annotations

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore
from mcp.server.fastmcp import FastMCP  # type: ignore

mcp = FastMCP("google-tasks-mcp")

TASKS_SCOPE = "https://www.googleapis.com/auth/tasks"


def _load_auth_config() -> dict[str, str]:
    path = os.environ.get("GOOGLE_TASKS_CREDENTIALS_JSON", "").strip()
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {k: str(v) for k, v in data.items() if v is not None}
    return {
        "client_id": os.environ.get("GOOGLE_TASKS_CLIENT_ID", "").strip(),
        "client_secret": os.environ.get("GOOGLE_TASKS_CLIENT_SECRET", "").strip(),
        "refresh_token": os.environ.get("GOOGLE_TASKS_REFRESH_TOKEN", "").strip(),
    }


def _credentials() -> Credentials:
    cfg = _load_auth_config()
    cid, secret, refresh = (
        cfg.get("client_id", ""),
        cfg.get("client_secret", ""),
        cfg.get("refresh_token", ""),
    )
    if not (cid and secret and refresh):
        raise RuntimeError(
            "Google Tasks auth missing. Set GOOGLE_TASKS_CLIENT_ID, "
            "GOOGLE_TASKS_CLIENT_SECRET, GOOGLE_TASKS_REFRESH_TOKEN, or "
            "GOOGLE_TASKS_CREDENTIALS_JSON with those keys."
        )
    token_uri = cfg.get("token_uri") or "https://oauth2.googleapis.com/token"
    return Credentials(
        token=None,
        refresh_token=refresh,
        token_uri=token_uri,
        client_id=cid,
        client_secret=secret,
        scopes=[TASKS_SCOPE],
    )


def _service():
    creds = _credentials()
    creds.refresh(Request())
    return build("tasks", "v1", credentials=creds, cache_discovery=False)


def _run_tool(fn):
    try:
        return json.dumps(fn(), indent=2, default=str)
    except Exception as e:
        return f"error: {e}"


@mcp.tool()
def tasks_list_tasklists(max_results: int = 100, page_token: str = "") -> str:
    """List the user's task lists (GET .../users/@me/lists).

    Args:
        max_results: Page size (max 1000).
        page_token: Pagination token from a previous response.
    """
    def go():
        svc = _service()
        kwargs: dict = {"maxResults": min(max(1, max_results), 1000)}
        if page_token.strip():
            kwargs["pageToken"] = page_token.strip()
        return svc.tasklists().list(**kwargs).execute()

    return _run_tool(go)


@mcp.tool()
def tasks_list_tasks(
    tasklist_id: str = "@default",
    max_results: int = 100,
    page_token: str = "",
    show_completed: bool = False,
    show_deleted: bool = False,
    show_hidden: bool = False,
    due_min_rfc3339: str = "",
    due_max_rfc3339: str = "",
) -> str:
    """List tasks in a task list.

    Args:
        tasklist_id: Task list id, or '@default' for the default list.
        max_results: Page size (max 100).
        page_token: Pagination token.
        show_completed: Include completed tasks.
        show_deleted: Include deleted tasks.
        show_hidden: Include hidden tasks.
        due_min_rfc3339: Lower bound for due date (RFC3339), e.g. 2026-03-30T00:00:00Z.
        due_max_rfc3339: Upper bound for due date (RFC3339).
    """
    def go():
        svc = _service()
        kwargs: dict = {
            "tasklist": tasklist_id,
            "maxResults": min(max(1, max_results), 100),
            "showCompleted": show_completed,
            "showDeleted": show_deleted,
            "showHidden": show_hidden,
        }
        if page_token.strip():
            kwargs["pageToken"] = page_token.strip()
        if due_min_rfc3339.strip():
            kwargs["dueMin"] = due_min_rfc3339.strip()
        if due_max_rfc3339.strip():
            kwargs["dueMax"] = due_max_rfc3339.strip()
        return svc.tasks().list(**kwargs).execute()

    return _run_tool(go)


@mcp.tool()
def tasks_get_task(tasklist_id: str, task_id: str) -> str:
    """Get a single task by id.

    Args:
        tasklist_id: Task list id.
        task_id: Task id.
    """
    def go():
        return (
            _service()
            .tasks()
            .get(tasklist=tasklist_id, task=task_id)
            .execute()
        )

    return _run_tool(go)


@mcp.tool()
def tasks_insert_task(
    tasklist_id: str,
    title: str,
    notes: str = "",
    due_rfc3339: str = "",
    parent: str = "",
    previous: str = "",
) -> str:
    """Create a task in a list (POST .../lists/{id}/tasks).

    Args:
        tasklist_id: Task list id.
        title: Task title (required).
        notes: Optional notes.
        due_rfc3339: Optional due datetime (RFC3339).
        parent: Optional parent task id for subtasks.
        previous: Optional task id to insert after (sibling ordering).
    """
    def go():
        body: dict = {"title": title}
        if notes.strip():
            body["notes"] = notes
        if due_rfc3339.strip():
            body["due"] = due_rfc3339.strip()
        kwargs: dict = {"tasklist": tasklist_id, "body": body}
        if parent.strip():
            kwargs["parent"] = parent.strip()
        if previous.strip():
            kwargs["previous"] = previous.strip()
        return _service().tasks().insert(**kwargs).execute()

    return _run_tool(go)


@mcp.tool()
def tasks_update_task(
    tasklist_id: str,
    task_id: str,
    title: str = "",
    notes: str = "",
    due_rfc3339: str = "",
    clear_due: bool = False,
    status: str = "",
    completed_rfc3339: str = "",
) -> str:
    """Patch a task (partial update).

    Args:
        tasklist_id: Task list id.
        task_id: Task id.
        title: New title (empty to leave unchanged).
        notes: New notes (empty to leave unchanged).
        due_rfc3339: New due datetime (RFC3339); empty unless clear_due or value set.
        clear_due: When True, remove the due date.
        status: 'needsAction' or 'completed', empty to leave unchanged.
        completed_rfc3339: Set completed timestamp (RFC3339) when completing.
    """
    def go():
        body: dict = {}
        if title.strip():
            body["title"] = title.strip()
        if notes != "":
            body["notes"] = notes
        if clear_due:
            body["due"] = None
        elif due_rfc3339.strip():
            body["due"] = due_rfc3339.strip()
        if status.strip():
            body["status"] = status.strip()
        if completed_rfc3339.strip():
            body["completed"] = completed_rfc3339.strip()
        if not body:
            return {"warning": "no fields to patch", "tasklist": tasklist_id, "task": task_id}
        return (
            _service()
            .tasks()
            .patch(tasklist=tasklist_id, task=task_id, body=body)
            .execute()
        )

    return _run_tool(go)


@mcp.tool()
def tasks_delete_task(tasklist_id: str, task_id: str) -> str:
    """Delete a task.

    Args:
        tasklist_id: Task list id.
        task_id: Task id.
    """
    def go():
        _service().tasks().delete(tasklist=tasklist_id, task=task_id).execute()
        return {"ok": True, "tasklist": tasklist_id, "task": task_id}

    return _run_tool(go)


@mcp.tool()
def tasks_clear_completed(tasklist_id: str) -> str:
    """Clear all completed tasks from a list.

    Args:
        tasklist_id: Task list id.
    """
    def go():
        return _service().tasks().clear(tasklist=tasklist_id).execute()

    return _run_tool(go)


if __name__ == "__main__":
    mcp.run(transport="stdio")
