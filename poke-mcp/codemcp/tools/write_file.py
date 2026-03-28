#!/usr/bin/env python3

import json
import os

from ..common import normalize_file_path
from ..file_utils import (
    check_file_path_and_permissions,
    write_text_content,
)
from ..git import commit_changes
from ..line_endings import detect_line_endings, detect_repo_line_endings
from ..mcp import mcp
from .commit_utils import append_commit_hash

__all__ = [
    "write_file",
]


@mcp.tool()
async def write_file(
    path: str,
    content: str | dict | list | None = None,
    description: str | None = None,
    commit_hash: str | None = None,
) -> str:
    """Write a file to the local filesystem. Overwrites the existing file if there is one.
    Provide a short description of the change.
    Changes are automatically committed to git after each write. Use commit_and_push when you are ready to push to remote.

    Before using this tool:

    1. Use the ReadFile tool to understand the file's contents and context

    2. Directory Verification (only applicable when creating new files):
       - Use the LS tool to verify the parent directory exists and is the correct location

    Args:
        path: The absolute path to the file to write
        content: The content to write to the file. Can be a string, dict, or list (will be converted to JSON)
        description: Short description of the change
        commit_hash: Optional Git commit hash for version tracking

    Returns:
        A success message

    Note:
        This function allows creating new files that don't exist yet.

    """
    # Set default values
    description = "" if description is None else description

    # Normalize the file path
    path = normalize_file_path(path)

    # Normalize content - if content is not a string, serialize it to a string using json.dumps
    if content is not None and not isinstance(content, str):
        content_str = json.dumps(content)
    else:
        content_str = content or ""

    # Normalize newlines
    content_str = (
        content_str.replace("\r\n", "\n")
        if isinstance(content_str, str)
        else content_str
    )

    # Validate file path and permissions
    is_valid, error_message = await check_file_path_and_permissions(path)
    if not is_valid:
        raise ValueError(error_message)

    # Determine line endings
    old_file_exists = os.path.exists(path)

    if old_file_exists:
        line_endings = await detect_line_endings(path)
    else:
        line_endings = detect_repo_line_endings(os.path.dirname(path))
        # Ensure directory exists for new files
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)

    # Write the content with UTF-8 encoding and proper line endings
    await write_text_content(path, content_str, "utf-8", line_endings)

    # Commit the changes
    git_message = ""
    success, message = await commit_changes(path, description)
    if success:
        git_message = f"\nChanges committed to git: {description}"
    else:
        git_message = f"\nFailed to commit changes to git: {message}"

    result = f"Successfully wrote to {path}{git_message}"

    # Append commit hash
    result, _ = await append_commit_hash(result, path, commit_hash)
    return result
