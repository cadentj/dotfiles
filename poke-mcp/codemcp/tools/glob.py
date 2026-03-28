#!/usr/bin/env python3

import fnmatch
import logging
import os
from typing import Any, Dict, List

from ..common import normalize_file_path
from ..git import is_git_repository
from ..mcp import mcp
from .commit_utils import append_commit_hash

__all__ = [
    "glob",
    "render_result_for_assistant",
]


def render_result_for_assistant(output: Dict[str, Any]) -> str:
    """Render the glob results in a format suitable for the assistant.

    Args:
        output: The output from the glob operation

    Returns:
        A formatted string representation of the results
    """
    filenames = output.get("files", [])
    num_files = output.get("total", 0)

    if num_files == 0:
        return "No files found"

    result = f"Found {num_files} files:\n\n"

    # Add each filename to the result
    for filename in filenames:
        result += f"{filename}\n"

    return result


@mcp.tool()
async def glob(
    pattern: str,
    path: str,
    limit: int | None = None,
    offset: int | None = None,
    chat_id: str | None = None,
    commit_hash: str | None = None,
) -> str:
    """Fast file pattern matching tool that works with any codebase size
    Supports glob patterns like "**/*.js" or "src/**/*.ts"
    Returns matching file paths sorted by modification time
    Use this tool when you need to find files by name patterns

    Args:
        pattern: The glob pattern to match files against
        path: The directory to search in
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
        chat_id: The unique ID of the current chat session
        commit_hash: Optional Git commit hash for version tracking

    Returns:
        A formatted string with the search results

    """
    try:
        # Set default values
        chat_id = "" if chat_id is None else chat_id
        limit_val = 100 if limit is None else limit
        offset_val = 0 if offset is None else offset

        # Normalize the directory path
        full_directory_path = normalize_file_path(path)

        # Validate the directory path
        if not os.path.exists(full_directory_path):
            raise FileNotFoundError(f"Directory does not exist: {path}")

        if not os.path.isdir(full_directory_path):
            raise NotADirectoryError(f"Path is not a directory: {path}")

        # Safety check: Verify the directory is within a git repository with codemcp.toml
        if not await is_git_repository(full_directory_path):
            raise ValueError(f"Directory is not in a Git repository: {path}")

        # Find all matching files
        matches: List[str] = []
        for root, dirs, files in os.walk(full_directory_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            # Check files against the pattern
            for file in files:
                if file.startswith("."):
                    continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, full_directory_path)

                if fnmatch.fnmatch(rel_path, pattern):
                    matches.append(rel_path)

        # Sort the matches
        matches.sort()

        # Apply offset and limit
        total_matches = len(matches)
        matches = matches[offset_val : offset_val + limit_val]

        # Create the result dictionary

        # Format the results
        if not matches:
            output = f"No files matching '{pattern}' found in {path}"
        else:
            output = f"Found {total_matches} files matching '{pattern}' in {path}"
            if offset_val > 0 or total_matches > offset_val + limit_val:
                output += f" (showing {offset_val + 1}-{min(offset_val + limit_val, total_matches)} of {total_matches})"
            output += ":\n\n"

            for match in matches:
                output += f"{match}\n"

        # Append commit hash
        result, _ = await append_commit_hash(output, full_directory_path, commit_hash)
        return result
    except Exception as e:
        # Log the error
        logging.error(f"Error in glob: {e}", exc_info=True)

        # Return error message
        error_message = f"Error searching for files: {e}"
        return error_message
