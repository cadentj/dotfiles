#!/usr/bin/env python3

import logging

from ..mcp import mcp

__all__ = [
    "think",
]


@mcp.tool()
async def think(
    thought: str, chat_id: str | None = None, commit_hash: str | None = None
) -> str:
    """Use the tool to think about something. It will not obtain new information or change the database,
    but just append the thought to the log. Use it when complex reasoning or some cache memory is needed.

    Args:
        thought: The thought to log
        chat_id: The unique ID of the current chat session
        commit_hash: Optional Git commit hash for version tracking

    Returns:
        A confirmation message that the thought was logged
    """
    # Set default values
    chat_id = "" if chat_id is None else chat_id

    # Log the thought but don't actually do anything with it
    logging.info(f"[{chat_id}] Thought: {thought}")

    # Return a simple confirmation message
    return f"Thought logged: {thought}"
