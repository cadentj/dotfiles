#!/usr/bin/env python3

import logging

from .git_parse_message import parse_message

__all__ = [
    "append_metadata_to_message",
    "update_commit_message_with_description",
]

log = logging.getLogger(__name__)


def append_metadata_to_message(message: str, metadata: dict[str, str]) -> str:
    """Append trailers to Git commit message

    Args:
        message: The original Git commit message
        metadata: Dictionary containing trailers; only codemcp-id is used

    Returns:
        The updated commit message with trailers added
    """
    from .git_parse_message import interpret_trailers

    trailers_to_add = [f"{k}: {v}" for k, v in metadata.items()]
    return interpret_trailers(message, trailers_to_add)


def update_commit_message_with_description(
    current_commit_message: str,
    description: str,
    commit_hash: str,
) -> str:
    """Update a commit message with a new description.

    This function handles the message munging logic for commit messages:
    - Updates the message by adding the description as a new entry
    - Uses marker tokens ```git-revs and ``` to demarcate commit list
    - Handles base revision markers and HEAD alignment

    Args:
        current_commit_message: The current Git commit message to update
        description: Description of the amend we're doing
        commit_hash: The current commit hash (used for updating HEAD entries and base revision)
        chat_id: The chat ID to ensure is in the metadata

    Returns:
        The updated commit message with the new description
    """
    # Define marker tokens for the commit list
    START_MARKER = "```git-revs"
    END_MARKER = "```"

    subject, main_message, trailers = parse_message(current_commit_message)

    # Extract the content parts (before, between, and after markers)
    start_marker_pos = main_message.find(START_MARKER)
    end_marker_pos = (
        main_message.find(END_MARKER, start_marker_pos + len(START_MARKER))
        if start_marker_pos != -1
        else -1
    )

    if start_marker_pos != -1 and end_marker_pos != -1:
        # Markers exist, extract the parts
        message_before = main_message[:start_marker_pos]
        rev_list_content = main_message[
            start_marker_pos + len(START_MARKER) : end_marker_pos
        ].strip()
        message_after = main_message[end_marker_pos + len(END_MARKER) :]

        # Parse the revision list
        rev_entries: list[str] = []
        if rev_list_content:
            rev_entries = [
                line.strip() for line in rev_list_content.splitlines() if line.strip()
            ]

        # Process rev_entries: replace any HEAD entries with actual commit hash
        has_base_revision = False
        new_rev_entries: list[str] = []

        for entry in rev_entries:
            if "(Base revision)" in entry:
                has_base_revision = True

            if entry.startswith("HEAD"):
                if commit_hash:
                    # Replace HEAD with commit hash
                    head_pos = entry.find("HEAD")
                    head_len = len("HEAD")

                    # Calculate the difference in length
                    len_diff = len(commit_hash) - head_len

                    # Replace HEAD with commit hash
                    prefix = entry[:head_pos]
                    suffix = entry[head_pos + head_len :]

                    # Adjust spacing if needed
                    if len_diff > 0 and suffix.startswith(" " * len_diff):
                        suffix = suffix[len_diff:]

                    new_entry = prefix + commit_hash + suffix
                    new_rev_entries.append(new_entry)
            else:
                new_rev_entries.append(entry)

        # Determine if we need to add a base revision marker
        if not has_base_revision and commit_hash:
            new_rev_entries.append(f"{commit_hash}  (Base revision)")

        # Add new HEAD entry if we have a description
        if description and commit_hash:
            # Calculate padding to align with commit hash
            head_padding = " " * (len(commit_hash) - 4)  # 4 is length of "HEAD"
            new_rev_entries.append(f"HEAD{head_padding}  {description}")

        # Reconstruct the rev list content
        formatted_rev_list = "\n".join(new_rev_entries)

        # Reconstruct the full message with markers
        main_message = f"{message_before}{START_MARKER}\n{formatted_rev_list}\n{END_MARKER}{message_after}"
    else:
        # Check for old format without markers - handle HEAD entries in the message
        lines = main_message.splitlines()
        has_base_revision = any("(Base revision)" in line for line in lines)
        has_head_entry = any(line.strip().startswith("HEAD") for line in lines)

        if has_head_entry or has_base_revision:
            # Old format detected, convert to new format with markers
            new_rev_entries: list[str] = []
            filtered_lines: list[str] = []

            for line in lines:
                if "(Base revision)" in line or line.strip().startswith("HEAD"):
                    # This is a revision entry, add to our rev entries
                    if line.strip():
                        if line.strip().startswith("HEAD") and commit_hash:
                            # Replace HEAD with commit hash
                            head_pos = line.find("HEAD")
                            head_len = len("HEAD")
                            len_diff = len(commit_hash) - head_len

                            prefix = line[:head_pos]
                            suffix = line[head_pos + head_len :]

                            if len_diff > 0 and suffix.startswith(" " * len_diff):
                                suffix = suffix[len_diff:]

                            new_line = prefix + commit_hash + suffix
                            new_rev_entries.append(new_line.strip())
                        else:
                            new_rev_entries.append(line.strip())
                else:
                    # Regular line, keep in message
                    filtered_lines.append(line)

            # Determine if we need to add a base revision marker
            if not has_base_revision and commit_hash:
                new_rev_entries.append(f"{commit_hash}  (Base revision)")

            # Add new HEAD entry if we have a description
            if description and commit_hash:
                head_padding = " " * (len(commit_hash) - 4)
                new_rev_entries.append(f"HEAD{head_padding}  {description}")

            # Format regular message without revision entries
            filtered_message = "\n".join(filtered_lines)

            # Format revision list
            formatted_rev_list = "\n".join(new_rev_entries)

            # Create new message with markers
            if filtered_message:
                if filtered_message.endswith("\n\n"):
                    main_message = f"{filtered_message}{START_MARKER}\n{formatted_rev_list}\n{END_MARKER}"
                elif filtered_message.endswith("\n"):
                    main_message = f"{filtered_message}\n{START_MARKER}\n{formatted_rev_list}\n{END_MARKER}"
                else:
                    main_message = f"{filtered_message}\n\n{START_MARKER}\n{formatted_rev_list}\n{END_MARKER}"
            else:
                main_message = f"{START_MARKER}\n{formatted_rev_list}\n{END_MARKER}"
        else:
            # No markers or HEAD entries, handle as normal
            if description:
                rev_entries: list[str] = []

                # If we have a commit hash, initialize with base revision
                if commit_hash:
                    rev_entries.append(f"{commit_hash}  (Base revision)")

                    # Add HEAD entry with description
                    head_padding = " " * (len(commit_hash) - 4)  # 4 is length of "HEAD"
                    rev_entries.append(f"HEAD{head_padding}  {description}")
                else:
                    # No commit hash, just add description without revision list
                    if main_message and not main_message.endswith("\n"):
                        main_message += "\n"
                    main_message += description

                    return main_message

                # Format the revision list with markers
                formatted_rev_list = "\n".join(rev_entries)

                # Add formatted revision list to the message
                if main_message:
                    # Ensure proper spacing
                    if main_message.endswith("\n\n"):
                        main_message += (
                            f"{START_MARKER}\n{formatted_rev_list}\n{END_MARKER}"
                        )
                    elif main_message.endswith("\n"):
                        main_message += (
                            f"\n{START_MARKER}\n{formatted_rev_list}\n{END_MARKER}"
                        )
                    else:
                        main_message += (
                            f"\n\n{START_MARKER}\n{formatted_rev_list}\n{END_MARKER}"
                        )
                else:
                    main_message = f"{START_MARKER}\n{formatted_rev_list}\n{END_MARKER}"

    return subject + "\n\n" + main_message + ("\n\n" + trailers if trailers else "")
