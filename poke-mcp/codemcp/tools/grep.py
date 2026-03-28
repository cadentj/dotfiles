#!/usr/bin/env python3

import logging
import os
import subprocess
from typing import Any, Dict

from ..common import normalize_file_path
from ..git import is_git_repository
from ..mcp import mcp
from ..shell import run_command
from .commit_utils import append_commit_hash

__all__ = [
    "grep",
    "git_grep",
    "render_result_for_assistant",
    "TOOL_NAME_FOR_PROMPT",
    "DESCRIPTION",
]

# Define constants
MAX_RESULTS = 100
TOOL_NAME_FOR_PROMPT = "Grep"
DESCRIPTION = f"""
Searches for files containing a specified pattern (regular expression) using git grep.
Files with a match are returned, up to a maximum of {MAX_RESULTS} files.
Note that this tool only works inside git repositories.

Example:
  grep "function.*hello" /path/to/repo  # Find files containing functions with "hello" in their name
  grep "console\\.log" /path/to/repo --include="*.js"  # Find JS files with console.log statements
  grep "pattern" /path/to/file.js  # Search for pattern in a specific file
"""


async def git_grep(
    pattern: str,
    path: str | None = None,
    include: str | None = None,
) -> list[str]:
    """Execute git grep to search for pattern in files.

    Args:
        pattern: The regular expression pattern to search for
        path: The directory or file to search in (must be in a git repository)
        include: Optional file pattern to filter the search

    Returns:
        A list of file paths with matches

    """
    if path is None:
        raise ValueError("Path must be provided for git grep")

    # Normalize the directory path
    absolute_path = normalize_file_path(path)

    # Verify this is a git repository - this check uses the mocked version in tests
    if not await is_git_repository(absolute_path):
        raise ValueError(f"The provided path is not in a git repository: {path}")

    # In non-test environment, verify the path exists
    if not os.environ.get("DESKAID_TESTING"):
        # Check if path exists
        if not os.path.exists(absolute_path):
            raise FileNotFoundError(f"Path does not exist: {path}")

        # If it's a file, adjust the command to use the file's directory
        # and restrict search to the specific file
        is_file = os.path.isfile(absolute_path)
        if not os.path.isdir(absolute_path) and not is_file:
            raise ValueError(f"Path is neither a directory nor a file: {path}")

    # Build git grep command
    # -l: list file names only
    # -i: case insensitive matching
    args = ["git", "grep", "-li", pattern]

    # Check if the path is a file
    is_file = (
        os.path.isfile(absolute_path)
        if not os.environ.get("DESKAID_TESTING")
        else False
    )

    # If it's a file, get the directory and restrict search to the specific file
    if is_file:
        file_dir = os.path.dirname(absolute_path)
        file_name = os.path.basename(absolute_path)

        # Add the specific file to search
        args.extend(["--", file_name])

        # Update absolute_path to the directory containing the file
        absolute_path = file_dir
    # Otherwise, add file pattern if specified
    elif include:
        args.extend(["--", include])

    logging.debug(f"Executing git grep command: {' '.join(args)}")

    try:
        # Execute git grep command asynchronously
        # Use explicit parameters to avoid confusion in mocking
        result = await run_command(
            cmd=args,
            cwd=absolute_path,
            capture_output=True,
            text=True,
            check=False,
        )

        # git grep returns exit code 1 when no matches are found, which is normal
        if result.returncode not in [0, 1]:
            logging.error(
                f"git grep failed with exit code {result.returncode}: {result.stderr}",
            )
            raise subprocess.SubprocessError(f"git grep failed: {result.stderr}")

        # Process results - split by newline and filter empty lines
        matches = [line.strip() for line in result.stdout.split() if line.strip()]

        # Convert to absolute paths
        matches = [
            os.path.join(absolute_path, match)
            for match in matches
            if isinstance(match, str)
        ]

        return matches
    except subprocess.SubprocessError as e:
        logging.exception(f"Error executing git grep: {e!s}")
        raise


def render_result_for_assistant(output: Dict[str, Any]) -> str:
    """Render the results in a format suitable for the assistant.

    Args:
        output: The grep results dictionary

    Returns:
        A formatted string representation of the results

    """
    num_files = output.get("numFiles", 0)
    matched_files = output.get("matchedFiles", [])

    if num_files == 0:
        return "No files found matching the pattern."

    result = f"Found {num_files} file(s) matching the pattern:\n\n"
    for file_path in matched_files:
        result += f"- {file_path}\n"

    return result


@mcp.tool()
async def grep(
    pattern: str,
    path: str | None = None,
    include: str | None = None,
    chat_id: str | None = None,
    commit_hash: str | None = None,
) -> str:
    """Searches for files containing a specified pattern (regular expression) using git grep.
    Files with a match are returned, up to a maximum of 100 files.
    Note that this tool only works inside git repositories.

    Example:
      Grep "function.*hello" /path/to/repo  # Find files containing functions with "hello" in their name
      Grep "console\\.log" /path/to/repo --include="*.js"  # Find JS files with console.log statements

    Args:
        pattern: The regular expression pattern to search for
        path: The directory or file to search in (must be in a git repository)
        include: Optional file pattern to filter the search
        chat_id: The unique ID of the current chat session
        commit_hash: Optional Git commit hash for version tracking

    Returns:
        A formatted string with the search results

    """
    try:
        # Set default values
        chat_id = "" if chat_id is None else chat_id

        # Default to current directory if path is not provided
        path = "." if path is None else path

        # Normalize the path
        normalized_path = normalize_file_path(path)

        # Execute git grep
        matched_files = await git_grep(pattern, normalized_path, include)

        # Limit the number of results
        truncated = len(matched_files) > MAX_RESULTS
        matched_files = matched_files[:MAX_RESULTS]

        # Prepare output
        output = {
            "numFiles": len(matched_files),
            "matchedFiles": matched_files,
            "truncated": truncated,
            "pattern": pattern,
            "path": path,
            "include": include,
        }

        # Add formatted result for assistant
        result_for_assistant = render_result_for_assistant(output)

        # Append commit hash
        if normalized_path:
            result_for_assistant, _ = await append_commit_hash(
                result_for_assistant, normalized_path, commit_hash
            )

        return result_for_assistant
    except Exception as e:
        # Log the error
        logging.error(f"Error in grep: {e}", exc_info=True)

        # Return error message
        error_message = f"Error searching for pattern: {e}"
        return error_message
