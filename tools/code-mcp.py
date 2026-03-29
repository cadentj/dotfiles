from mcp.server.fastmcp import FastMCP # type: ignore
import os
import re
import subprocess
from edit import apply_edit_with_fallback

mcp = FastMCP("code-mcp")
MAX_OUTPUT_CHARS = 120_000
MAX_OUTPUT_LINES = 2_000


def _truncate_text(text: str) -> str:
    lines = text.splitlines()
    if len(lines) > MAX_OUTPUT_LINES:
        lines = lines[:MAX_OUTPUT_LINES]
    out = "\n".join(lines)
    if len(out) > MAX_OUTPUT_CHARS:
        out = out[:MAX_OUTPUT_CHARS]
    return out


@mcp.tool()
def ls(path: str = ".") -> str:
    """List files/directories in a path.

    Args:
        path: Directory path to list.
    """
    p = os.path.abspath(path)
    return "\n".join(sorted(os.listdir(p)))


@mcp.tool()
def glob(
    pattern: str,
    path: str = ".",
    limit: int = 100,
    offset: int = 0,
) -> str:
    """Find files by glob pattern using ripgrep file listing.

    Args:
        pattern: Glob pattern to match.
        path: Base directory to search.
        limit: Max result count.
        offset: Result start offset.
    """
    base = os.path.abspath(path)
    cmd = ["rg", "--files", "--hidden", "--glob", pattern]
    out = subprocess.run(cmd, cwd=base, capture_output=True, text=True).stdout
    rel = [line for line in out.splitlines() if line.strip()]
    matches = [os.path.join(base, line) for line in rel]
    matches.sort()
    return "\n".join(matches[offset : offset + limit])


@mcp.tool()
def grep(
    pattern: str,
    path: str = ".",
    include: str | None = None,
    before: int = 2,
    after: int = 2,
) -> str:
    """Search file contents with ripgrep. Use before/after for context lines.

    Args:
        pattern: Regex pattern.
        path: Search path.
        include: Optional file glob filter.
        before: Context lines before each hit.
        after: Context lines after each hit.
    """
    p = os.path.abspath(path)
    cmd = ["rg", "-nH"]
    if before:
        cmd += ["-B", str(before)]
    if after:
        cmd += ["-A", str(after)]
    if include:
        cmd += ["--glob", include]
    cmd += [pattern, p]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    return _truncate_text(out)


@mcp.tool()
def read(
    filePath: str,
    offset: int = 1,
    limit: int = 500,
) -> str:
    """Read a file and return numbered lines.

    Args:
        filePath: File path to read.
        offset: 1-indexed start line.
        limit: Maximum lines to return.
    """
    p = os.path.abspath(filePath)
    lines = open(p, "r", encoding="utf-8").read().splitlines()
    start = offset - 1
    chunk = lines[start : start + limit]
    out = "\n".join(f"{i + offset}: {line}" for i, line in enumerate(chunk))
    return _truncate_text(out)


@mcp.tool()
def edit(
    filePath: str,
    oldString: str,
    newString: str,
    replaceAll: bool = False,
) -> str:
    """Edit a file with fallback matching strategies.

    Args:
        filePath: File path to modify.
        oldString: Text to replace.
        newString: Replacement text.
        replaceAll: Replace all exact matches when true.
    """
    p = os.path.abspath(filePath)
    content = open(p, "r", encoding="utf-8").read()
    updated, n = apply_edit_with_fallback(content, oldString, newString, replaceAll)
    open(p, "w", encoding="utf-8").write(updated)
    return f"ok ({n} replacements)"


@mcp.tool()
def replace_regex(
    filePath: str,
    pattern: str,
    repl: str,
    count: int = 0,
    flags: str = "",
) -> str:
    """Replace text using a regex pattern.

    Args:
        filePath: File path to modify.
        pattern: Regex pattern.
        repl: Replacement string.
        count: Max replacement count, 0 for unlimited.
        flags: Regex flags (i, m, s).
    """
    p = os.path.abspath(filePath)
    content = open(p, "r", encoding="utf-8").read()
    re_flags = 0
    if "i" in flags:
        re_flags |= re.IGNORECASE
    if "m" in flags:
        re_flags |= re.MULTILINE
    if "s" in flags:
        re_flags |= re.DOTALL
    updated, n = re.subn(pattern, repl, content, count=count, flags=re_flags)
    open(p, "w", encoding="utf-8").write(updated)
    return f"ok ({n} replacements)"


@mcp.tool()
def write(filePath: str, content: str) -> str:
    """Write full file content (create or overwrite).

    Args:
        filePath: File path to write.
        content: Full file content.
    """
    p = os.path.abspath(filePath)
    open(p, "w", encoding="utf-8").write(content)
    return "ok"


if __name__ == "__main__":
    mcp.run(transport="stdio")
