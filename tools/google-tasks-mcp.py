"""MCP server for Google Tasks API v1 (REST).

Works with any Google account that has Google Tasks (personal @gmail.com or
Google Workspace); the API is not Workspace-only.

Auth (pick one approach):

1) Env vars: GOOGLE_TASKS_CLIENT_ID, GOOGLE_TASKS_CLIENT_SECRET,
   GOOGLE_TASKS_REFRESH_TOKEN (after a one-time OAuth with scope
   https://www.googleapis.com/auth/tasks).

2) Single JSON file via GOOGLE_TASKS_CREDENTIALS_JSON: either the flat shape
   {client_id, client_secret, refresh_token} or merge the OAuth *client* JSON
   you download from Google Cloud (top-level "installed" or "web" object) with
   a sibling "refresh_token" key you add after running the OAuth flow once.

3) Two files (matches the usual Console download + token pattern):
   GOOGLE_TASKS_CLIENT_SECRETS_JSON = path to the downloaded client secret JSON
   (unchanged; contains "installed" or "web").
   GOOGLE_TASKS_TOKEN_JSON = path to a small JSON file with at least
   {"refresh_token": "..."} (e.g. copy from oauth-setup output).

Env vars override values loaded from files when set.
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
DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"


def _client_from_installed_or_web(data: dict) -> dict[str, str]:
    for key in ("installed", "web"):
        block = data.get(key)
        if not isinstance(block, dict):
            continue
        cid = block.get("client_id") or ""
        secret = block.get("client_secret") or ""
        token_uri = block.get("token_uri") or DEFAULT_TOKEN_URI
        if cid and secret:
            return {
                "client_id": str(cid),
                "client_secret": str(secret),
                "token_uri": str(token_uri),
            }
    return {}


def _dict_from_json_file(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return raw if isinstance(raw, dict) else {}


def _load_auth_config() -> dict[str, str]:
    cfg: dict[str, str] = {}

    combined = os.environ.get("GOOGLE_TASKS_CREDENTIALS_JSON", "").strip()
    if combined and os.path.isfile(combined):
        data = _dict_from_json_file(combined)
        cfg.update(_client_from_installed_or_web(data))
        for k in ("client_id", "client_secret", "refresh_token", "token_uri"):
            v = data.get(k)
            if v is not None and str(v).strip():
                cfg[k] = str(v).strip()

    client_path = os.environ.get("GOOGLE_TASKS_CLIENT_SECRETS_JSON", "").strip()
    if client_path and os.path.isfile(client_path):
        data = _dict_from_json_file(client_path)
        extracted = _client_from_installed_or_web(data)
        if extracted:
            cfg.update(extracted)
        else:
            for k in ("client_id", "client_secret"):
                v = data.get(k)
                if v is not None and str(v).strip():
                    cfg[k] = str(v).strip()
            if data.get("token_uri"):
                cfg["token_uri"] = str(data["token_uri"]).strip()

    token_path = os.environ.get("GOOGLE_TASKS_TOKEN_JSON", "").strip()
    if token_path and os.path.isfile(token_path):
        data = _dict_from_json_file(token_path)
        rt = data.get("refresh_token")
        if rt is not None and str(rt).strip():
            cfg["refresh_token"] = str(rt).strip()

    if os.environ.get("GOOGLE_TASKS_CLIENT_ID", "").strip():
        cfg["client_id"] = os.environ["GOOGLE_TASKS_CLIENT_ID"].strip()
    if os.environ.get("GOOGLE_TASKS_CLIENT_SECRET", "").strip():
        cfg["client_secret"] = os.environ["GOOGLE_TASKS_CLIENT_SECRET"].strip()
    if os.environ.get("GOOGLE_TASKS_REFRESH_TOKEN", "").strip():
        cfg["refresh_token"] = os.environ["GOOGLE_TASKS_REFRESH_TOKEN"].strip()

    return cfg


def _credentials() -> Credentials:
    cfg = _load_auth_config()
    cid, secret, refresh = (
        cfg.get("client_id", ""),
        cfg.get("client_secret", ""),
        cfg.get("refresh_token", ""),
    )
    if not (cid and secret and refresh):
        raise RuntimeError(
            "Google Tasks auth missing. Use env CLIENT_ID/SECRET/REFRESH_TOKEN, or "
            "GOOGLE_TASKS_CREDENTIALS_JSON (flat or client JSON + refresh_token), or "
            "GOOGLE_TASKS_CLIENT_SECRETS_JSON + GOOGLE_TASKS_TOKEN_JSON "
            '(token file: {"refresh_token": "..."}).'
        )
    token_uri = cfg.get("token_uri") or DEFAULT_TOKEN_URI
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
