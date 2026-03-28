#!/usr/bin/env python3

"""Module for line ending detection and handling."""

import asyncio
import os
from pathlib import Path
from typing import Literal, Optional

import tomli
from editorconfig import get_properties

from .glob_pattern import match as glob_match

__all__ = [
    "get_line_ending_preference",
    "normalize_to_lf",
    "apply_line_endings",
    "detect_line_endings",
    "detect_repo_line_endings",
]


def normalize_to_lf(content: str) -> str:
    """Normalize all line endings to LF (\n).

    Args:
        content: The text content to normalize

    Returns:
        Text with all line endings normalized to LF
    """
    # First replace CRLF with LF
    normalized = content.replace("\r\n", "\n")
    # Then handle any lone CR characters
    normalized = normalized.replace("\r", "\n")
    return normalized


def apply_line_endings(content: str, line_ending: str | None) -> str:
    """Apply the specified line ending to the content.

    Args:
        content: The text content with LF line endings
        line_ending: The line ending to apply ('CRLF', 'LF', '\r\n', or '\n')
                    If None, defaults to LF

    Returns:
        Text with specified line endings
    """
    # Default to LF if line_ending is None
    if line_ending is None:
        actual_line_ending = "\n"
    # Convert line ending format string to actual character sequence
    elif line_ending.upper() == "CRLF":
        actual_line_ending = "\r\n"
    elif line_ending.upper() == "LF":
        actual_line_ending = "\n"
    else:
        # Assume it's already the character sequence
        actual_line_ending = line_ending

    # First normalize the content (ensure it uses only \n)
    normalized = normalize_to_lf(content)

    # Then replace with the specified line ending if it's not LF
    if actual_line_ending != "\n":
        return normalized.replace("\n", actual_line_ending)

    return normalized


def check_editorconfig(file_path: str) -> Optional[str]:
    """Check .editorconfig file for line ending preferences using the official editorconfig library.

    Args:
        file_path: The path to the file being edited

    Returns:
        'CRLF' or 'LF' if specified in .editorconfig, None otherwise
    """
    # Use the official editorconfig library to get properties
    options = get_properties(file_path)

    # Check if end_of_line is specified
    if "end_of_line" in options:
        eol_value = options["end_of_line"].lower()
        if eol_value == "crlf":
            return "CRLF"
        elif eol_value == "lf":
            return "LF"
        # Ignore other values (like CR)

    return None


def check_gitattributes(file_path: str) -> Optional[str]:
    """Check .gitattributes file for line ending preferences.

    Args:
        file_path: The path to the file being edited

    Returns:
        'CRLF' or 'LF' if specified in .gitattributes, None otherwise
    """
    try:
        # Use the Path object to navigate up the directory tree
        path = Path(file_path)
        file_dir = path.parent
        relative_path = path.name

        # Iterate up through parent directories looking for .gitattributes
        current_dir = file_dir
        while current_dir != current_dir.parent:  # Stop at the root directory
            gitattributes_path = current_dir / ".gitattributes"
            if gitattributes_path.exists():
                # Found a .gitattributes file
                with open(gitattributes_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # Process lines in reverse to prioritize more specific patterns
                for line in reversed(lines):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    parts = line.split()
                    if len(parts) < 2:
                        continue

                    pattern, attrs = parts[0], parts[1:]

                    # Use glob.match to check if the pattern matches the file
                    # Git patterns behave like gitignore patterns, so we don't enable editorconfig features
                    if pattern == "*" or glob_match(
                        pattern, relative_path, editorconfig=False
                    ):
                        # Check for text/eol attributes
                        for attr in attrs:
                            if attr == "text=auto":
                                # Use auto line endings (preserve)
                                pass
                            elif attr == "eol=crlf":
                                return "CRLF"
                            elif attr == "eol=lf":
                                return "LF"
                            elif attr == "text":
                                # Default to LF for text files
                                return "LF"
                            elif attr == "-text" or attr == "binary":
                                # Binary files should preserve line endings
                                return None

                # If we found a .gitattributes but couldn't determine the line ending,
                # stop searching (don't check parent dirs)
                break

            # Move up to the parent directory
            current_dir = current_dir.parent

    except Exception:
        pass  # Ignore any errors in parsing .gitattributes

    return None


def check_codemcp_toml(file_path: str) -> Optional[str]:
    """Check codemcp.toml file for line ending preferences.

    Args:
        file_path: The path to the file being edited

    Returns:
        'CRLF' or 'LF' if specified in codemcp.toml, None otherwise
    """
    try:
        # Use the Path object to navigate up the directory tree
        path = Path(file_path)
        file_dir = path.parent

        # Iterate up through parent directories looking for codemcp.toml
        current_dir = file_dir
        while current_dir != current_dir.parent:  # Stop at the root directory
            codemcp_toml_path = current_dir / "codemcp.toml"
            if codemcp_toml_path.exists():
                # Found a codemcp.toml file
                with open(codemcp_toml_path, "rb") as f:
                    config = tomli.load(f)

                # Check for line_endings setting
                if "files" in config and "line_endings" in config["files"]:
                    line_endings = config["files"]["line_endings"]
                    if line_endings.upper() in ("CRLF", "LF"):
                        return line_endings.upper()

                # If we found a codemcp.toml but couldn't determine the line ending,
                # stop searching (don't check parent dirs)
                break

            # Move up to the parent directory
            current_dir = current_dir.parent

    except Exception:
        pass  # Ignore any errors in parsing codemcp.toml

    return None


def check_codemcprc() -> Optional[str]:
    """Check user's ~/.codemcprc file for line ending preferences.

    Returns:
        'CRLF' or 'LF' if specified in ~/.codemcprc, None otherwise
    """
    try:
        from .config import get_line_endings_preference

        line_endings = get_line_endings_preference()
        if line_endings and line_endings.upper() in ("CRLF", "LF"):
            return line_endings.upper()

    except Exception:
        pass  # Ignore any errors in parsing ~/.codemcprc

    return None


def get_line_ending_preference(file_path: str) -> str:
    """Determine the preferred line ending style for a file.

    Checks configuration sources in the following order:
    1. .editorconfig
    2. .gitattributes
    3. codemcp.toml
    4. ~/.codemcprc
    5. Default to OS native line ending if not specified elsewhere

    Args:
        file_path: The path to the file being edited

    Returns:
        The character sequence to use for line endings ('\r\n' or '\n')
    """
    # Check .editorconfig first
    line_ending = check_editorconfig(file_path)
    if line_ending:
        return "\r\n" if line_ending == "CRLF" else "\n"

    # Then check .gitattributes
    line_ending = check_gitattributes(file_path)
    if line_ending:
        return "\r\n" if line_ending == "CRLF" else "\n"

    # Then check codemcp.toml
    line_ending = check_codemcp_toml(file_path)
    if line_ending:
        return "\r\n" if line_ending == "CRLF" else "\n"

    # Then check ~/.codemcprc
    line_ending = check_codemcprc()
    if line_ending:
        return "\r\n" if line_ending == "CRLF" else "\n"

    # Default to OS native line ending
    return os.linesep


async def detect_line_endings(
    file_path: str, return_format: Literal["str", "format"] = "str"
) -> str:
    """Detect the line endings of a file.

    Args:
        file_path: The path to the file
        return_format: Return format - either "str" for actual characters ("\n" or "\r\n")
                      or "format" for "LF" or "CRLF" strings

    Returns:
        The detected line endings ('\n' or '\r\n') or ('LF' or 'CRLF') based on return_format
    """
    if not os.path.exists(file_path):
        line_ending = get_line_ending_preference(file_path)
        return (
            "LF"
            if line_ending == "\n"
            else "CRLF"
            if return_format == "format"
            else line_ending
        )

    loop = asyncio.get_event_loop()

    def read_and_detect():
        try:
            with open(file_path, "rb") as f:
                content = f.read(4096)  # Read a sample chunk
                if b"\r\n" in content:
                    return "CRLF" if return_format == "format" else "\r\n"
                return "LF" if return_format == "format" else "\n"
        except Exception:
            # If there's an error reading the file, use the line ending preference
            line_ending = get_line_ending_preference(file_path)
            return (
                "LF"
                if line_ending == "\n"
                else "CRLF"
                if return_format == "format"
                else line_ending
            )

    return await loop.run_in_executor(None, read_and_detect)


def detect_repo_line_endings(
    directory: str, return_format: Literal["str", "format"] = "str"
) -> str:
    """Detect the line endings to use for new files in a repository.

    Args:
        directory: The repository directory
        return_format: Return format - either "str" for actual characters ("\n" or "\r\n")
                      or "format" for "LF" or "CRLF" strings

    Returns:
        The line endings to use ('\n' or '\r\n') or ('LF' or 'CRLF') based on return_format
    """
    # Create a dummy path inside the directory to check configuration
    dummy_path = os.path.join(directory, "dummy.txt")
    line_ending = get_line_ending_preference(dummy_path)
    return (
        "LF"
        if line_ending == "\n"
        else "CRLF"
        if return_format == "format"
        else line_ending
    )
