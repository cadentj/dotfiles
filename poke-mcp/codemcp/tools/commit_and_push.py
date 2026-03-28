#!/usr/bin/env python3

import logging

from ..common import normalize_file_path
from ..git import commit_changes, get_repository_root, is_git_repository
from ..mcp import mcp
from ..shell import run_command

__all__ = [
    "commit_and_push",
]

log = logging.getLogger(__name__)


@mcp.tool()
async def commit_and_push(
    path: str,
    message: str | None = None,
) -> str:
    """Stage all changes, commit, and push to the remote repository.

    Use this tool when you are done making changes and want to push them
    to the remote (e.g. GitHub).  It will:
      1. ``git add -A`` (stage everything)
      2. ``git commit`` with the provided message (skipped if nothing to commit)
      3. ``git push`` to the current tracking branch

    Args:
        path: An absolute path inside the repository (used to locate the repo root).
        message: Commit message.  If omitted or empty, uses a default message.

    Returns:
        A summary of what happened (committed, pushed, etc.)

    """
    full_path = normalize_file_path(path)

    if not await is_git_repository(full_path):
        raise ValueError(f"Path is not in a Git repository: {path}")

    git_cwd = await get_repository_root(full_path)

    # Stage + commit (reuse existing helper)
    commit_msg = (message or "").strip() or "codemcp: update"
    success, commit_result = await commit_changes(git_cwd, commit_msg)

    parts: list[str] = []
    if success and "No changes to commit" not in commit_result:
        parts.append(commit_result)
    elif not success:
        return f"Commit failed: {commit_result}"
    else:
        parts.append("Nothing new to commit.")

    # Push
    push_result = await run_command(
        ["git", "push"],
        cwd=git_cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    if push_result.returncode != 0:
        stderr = push_result.stderr.strip()
        assert isinstance(stderr, str)
        if "no upstream branch" in stderr or "has no upstream" in stderr:
            # Try push with --set-upstream for the current branch
            branch_result = await run_command(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            branch = branch_result.stdout.strip()
            assert isinstance(branch, str)
            push_result = await run_command(
                ["git", "push", "--set-upstream", "origin", branch],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
            if push_result.returncode != 0:
                parts.append(f"Push failed: {push_result.stderr.strip()}")
                return "\n".join(parts)

        else:
            parts.append(f"Push failed: {stderr}")
            return "\n".join(parts)

    parts.append("Pushed to remote successfully.")
    return "\n".join(parts)
