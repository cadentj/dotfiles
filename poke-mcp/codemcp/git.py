#!/usr/bin/env python3

# This file re-exports functions from git_*.py modules for backward compatibility

from .git_commit import commit_changes
from .git_query import (
    get_head_commit_hash,
    get_repository_root,
    is_git_repository,
)

__all__ = [
    "get_head_commit_hash",
    "get_repository_root",
    "is_git_repository",
    "commit_changes",
]
