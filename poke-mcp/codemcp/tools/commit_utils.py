#!/usr/bin/env python3

import logging
from typing import Tuple

from ..common import normalize_file_path
from ..git_query import get_current_commit_hash

__all__ = [
    "append_commit_hash",
]


async def append_commit_hash(
    result: str, path: str | None, commit_hash: str | None = None
) -> Tuple[str, str | None]:
    """Get the current Git commit hash and append it to the result string.

    Args:
        result: The original result string to append to
        path: Path to the Git repository (if available)
        commit_hash: Optional Git commit hash to use instead of fetching the current one

    Returns:
        A tuple containing:
            - The result string with the commit hash appended
            - The current commit hash if available, None otherwise
    """
    # If commit_hash is provided, use it directly
    if commit_hash:
        return f"{result}\n\nCurrent commit hash: {commit_hash}", commit_hash

    if path is None:
        return result, None

    # Normalize the path
    normalized_path = normalize_file_path(path)

    try:
        current_hash = await get_current_commit_hash(normalized_path)
        if current_hash:
            return f"{result}\n\nCurrent commit hash: {current_hash}", current_hash
    except Exception as e:
        logging.warning(f"Failed to get current commit hash: {e}", exc_info=True)

    return result, None
