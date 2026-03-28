#!/usr/bin/env python3

import logging
import os

from .git_query import get_head_commit_hash, is_git_repository
from .shell import run_command

__all__ = ["commit_changes"]

log = logging.getLogger(__name__)


async def commit_changes(
    path: str,
    description: str,
    commit_all: bool = False,
) -> tuple[bool, str]:
    """Stage all changes in the repository and create a new commit.

    Runs ``git add -A`` at the repository root, then ``git commit -m``.

    Args:
        path: A file or directory path inside the repo (used to locate the repo root).
        description: Commit message (defaults to a generic message if empty).
        commit_all: Ignored; staging is always repository-wide via ``git add -A``.

    Returns:
        A tuple of (success, message)

    """
    _ = commit_all  # legacy parameter; staging is always repo-wide
    log.debug("commit_changes(%s, %s)", path, description)

    if not await is_git_repository(path):
        return False, f"Path '{path}' is not in a Git repository"

    abs_path = os.path.abspath(path)
    directory = os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path

    if os.path.isfile(abs_path) and not os.path.exists(abs_path):
        return False, f"File does not exist: {abs_path}"

    from .git_query import get_repository_root

    git_cwd = await get_repository_root(directory)

    add_result = await run_command(
        ["git", "add", "-A"],
        cwd=git_cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if add_result.returncode != 0:
        return False, f"Failed to stage changes: {add_result.stderr}"

    diff_result = await run_command(
        ["git", "diff", "--cached", "--quiet"],
        cwd=git_cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if diff_result.returncode == 0:
        return True, "No changes to commit (changes already committed or no changes detected)"

    msg = description.strip() if description.strip() else "codemcp: update"
    commit_result = await run_command(
        ["git", "commit", "--no-gpg-sign", "-m", msg],
        cwd=git_cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if commit_result.returncode != 0:
        return False, f"Failed to commit: {commit_result.stderr}"

    prev_hash = await get_head_commit_hash(git_cwd, short=True)
    return True, f"Changes committed successfully (commit {prev_hash})"
