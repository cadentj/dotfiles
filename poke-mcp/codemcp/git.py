#!/usr/bin/env python3

# This file re-exports functions from git_*.py modules for backward compatibility

from .git_commit import commit_changes, create_commit_reference
from .git_message import append_metadata_to_message
from .git_query import (
    get_head_commit_chat_id,
    get_head_commit_hash,
    get_head_commit_message,
    get_ref_commit_chat_id,
    get_repository_root,
    is_git_repository,
)

__all__ = [
    # From git_query.py
    "get_head_commit_message",
    "get_head_commit_hash",
    "get_head_commit_chat_id",
    "get_repository_root",
    "is_git_repository",
    "get_ref_commit_chat_id",
    # From git_message.py
    "append_metadata_to_message",
    # From git_commit.py
    "commit_changes",
    "create_commit_reference",
]
