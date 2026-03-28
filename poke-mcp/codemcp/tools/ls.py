#!/usr/bin/env python3

import asyncio
import os
from typing import List, Optional

from ..access import check_edit_permission
from ..common import normalize_file_path
from ..git import is_git_repository
from ..mcp import mcp
from .commit_utils import append_commit_hash

__all__ = [
    "ls",
    "list_directory",
    "skip",
    "TreeNode",
    "create_file_tree",
    "print_tree",
    "MAX_FILES",
]

MAX_FILES = 1000
TRUNCATED_MESSAGE = f"There are more than {MAX_FILES} files in the directory. Use more specific paths to explore nested directories. The first {MAX_FILES} files and directories are included below:\n\n"


@mcp.tool()
async def ls(
    path: str, chat_id: str | None = None, commit_hash: str | None = None
) -> str:
    """Lists files and directories in a given path. The path parameter must be an absolute path, not a relative path.
    You should generally prefer the Glob and Grep tools, if you know which directories to search.

    Args:
        path: The absolute path to the directory to list
        chat_id: The unique ID of the current chat session
        commit_hash: Optional Git commit hash for version tracking

    Returns:
        A formatted string representation of the directory contents

    """
    # Set default values
    chat_id = "" if chat_id is None else chat_id

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

    # Check edit permission (which verifies codemcp.toml exists)
    is_permitted, permission_message = await check_edit_permission(full_directory_path)
    if not is_permitted:
        raise ValueError(permission_message)

    # Get the directory contents asynchronously
    results = await list_directory(full_directory_path)

    # Sort the results
    results.sort()

    # Create a file tree and print it
    tree = create_file_tree(results)
    tree_output = print_tree(tree, cwd=full_directory_path)

    # Return the result with truncation message if needed
    output = tree_output
    if len(results) >= MAX_FILES:
        output = f"{TRUNCATED_MESSAGE}{tree_output}"

    # Append commit hash
    result, _ = await append_commit_hash(output, full_directory_path, commit_hash)
    return result


async def list_directory(initial_path: str) -> List[str]:
    """List all files and directories recursively.

    Args:
        initial_path: The path to start listing from

    Returns:
        A list of relative paths to files and directories

    """
    results: List[str] = []
    loop = asyncio.get_event_loop()

    # Use a function to perform the directory listing asynchronously
    async def list_dir_async() -> List[str]:
        queue: List[str] = [initial_path]
        while queue and len(results) <= MAX_FILES:
            path = queue.pop(0)

            if skip(path) and path != initial_path:
                continue

            if path != initial_path:
                # Add directories with trailing slash
                rel_path = os.path.relpath(path, initial_path)
                if os.path.isdir(path):
                    rel_path = f"{rel_path}{os.sep}"
                results.append(rel_path)

            if os.path.isdir(path):
                try:
                    # Get directory listing asynchronously
                    children = await loop.run_in_executor(
                        None, lambda: os.listdir(path)
                    )
                    for child in children:
                        child_path = os.path.join(path, child)
                        if os.path.isdir(child_path):
                            queue.append(child_path)
                        elif not skip(child_path):
                            rel_path = os.path.relpath(child_path, initial_path)
                            results.append(rel_path)
                            if len(results) > MAX_FILES:
                                return results
                except (PermissionError, OSError):
                    # Skip directories we can't access
                    continue

        return results

    return await list_dir_async()


def skip(path: str) -> bool:
    """Determine if a path should be skipped.

    Args:
        path: The path to check

    Returns:
        True if the path should be skipped, False otherwise

    """
    basename = os.path.basename(path)
    if path != "." and basename.startswith("."):
        return True
    if "__pycache__" in path:
        return True
    return False


class TreeNode:
    """A node in a file tree."""

    def __init__(self, name: str, path: str, node_type: str):
        self.name = name
        self.path = path
        self.type = node_type
        self.children: List[TreeNode] = []


def create_file_tree(sorted_paths: List[str]) -> List[TreeNode]:
    """Create a file tree from a list of paths.

    Args:
        sorted_paths: A list of sorted relative paths

    Returns:
        A list of TreeNode objects representing the root of the tree

    """
    root: List[TreeNode] = []

    for path in sorted_paths:
        parts = path.split(os.sep)
        current_level = root
        current_path = ""

        for i, part in enumerate(parts):
            if not part:  # Skip empty parts (trailing slashes)
                continue

            current_path = os.path.join(current_path, part) if current_path else part
            is_last_part = i == len(parts) - 1

            # Check if this node already exists at this level
            existing_node: Optional[TreeNode] = None
            for node in current_level:
                if node.name == part:
                    existing_node = node
                    break

            if existing_node:
                current_level = existing_node.children
            else:
                # Create a new node
                node_type = (
                    "file"
                    if is_last_part and not path.endswith(os.sep)
                    else "directory"
                )
                new_node = TreeNode(part, current_path, node_type)
                current_level.append(new_node)
                current_level = new_node.children

    return root


def print_tree(
    tree: List[TreeNode],
    level: int = 0,
    prefix: str = "",
    cwd: str = "",
) -> str:
    """Print a file tree.

    Args:
        tree: A list of TreeNode objects
        level: The current level in the tree
        prefix: The prefix to use for indentation
        cwd: The current working directory

    Returns:
        A formatted string representation of the tree

    """
    result = ""

    # Add absolute path at root level
    if level == 0:
        result += f"- {cwd}{os.sep}\n"
        prefix = "  "

    for node in tree:
        # Add the current node to the result
        node_suffix = f"{os.sep}" if node.type == "directory" else ""
        result += f"{prefix}{'-'} {node.name}{node_suffix}\n"

        # Recursively print children
        if node.children:
            result += print_tree(node.children, level + 1, f"{prefix}  ", cwd)

    return result
