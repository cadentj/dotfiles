import math
import re
from difflib import SequenceMatcher


def _replace_whitespace_tolerant(content: str, old: str, new: str) -> tuple[str, int]:
    whole_lines = content.splitlines(keepends=True)
    part_lines = old.splitlines(keepends=True)
    if not part_lines:
        return content, 0
    candidates: list[int] = []
    for i in range(len(whole_lines) - len(part_lines) + 1):
        chunk = whole_lines[i : i + len(part_lines)]
        if all(a.rstrip() == b.rstrip() for a, b in zip(chunk, part_lines, strict=False)):
            candidates.append(i)
    if len(candidates) != 1:
        return content, 0
    i = candidates[0]
    replace_lines = new.splitlines(keepends=True)
    updated = "".join(whole_lines[:i] + replace_lines + whole_lines[i + len(part_lines) :])
    return updated, 1


def _try_dotdotdots(content: str, old: str, new: str) -> tuple[str, int]:
    dots_re = re.compile(r"(^\s*\.\.\.\s*$\n?)", re.MULTILINE)
    old_pieces = re.split(dots_re, old)
    new_pieces = re.split(dots_re, new)
    if len(old_pieces) == 1:
        return content, 0
    if len(old_pieces) != len(new_pieces):
        return content, 0
    if not all(old_pieces[i] == new_pieces[i] for i in range(1, len(old_pieces), 2)):
        return content, 0

    old_blocks = [old_pieces[i] for i in range(0, len(old_pieces), 2)]
    new_blocks = [new_pieces[i] for i in range(0, len(new_pieces), 2)]

    updated = content
    replacements = 0
    for old_block, new_block in zip(old_blocks, new_blocks, strict=False):
        if not old_block and new_block:
            if updated and not updated.endswith("\n"):
                updated += "\n"
            updated += new_block
            replacements += 1
            continue
        if not old_block:
            continue
        if updated.count(old_block) != 1:
            return content, 0
        updated = updated.replace(old_block, new_block, 1)
        replacements += 1
    return updated, replacements


def _replace_fuzzy(content: str, old: str, new: str, similarity_threshold: float = 0.8) -> tuple[str, int]:
    whole_lines = content.splitlines(keepends=True)
    part_lines = old.splitlines(keepends=True)
    if not part_lines:
        return content, 0

    min_len = max(1, math.floor(len(part_lines) * 0.9))
    max_len = max(min_len, math.ceil(len(part_lines) * 1.1))
    best_ratio = 0.0
    best_start = -1
    best_end = -1

    for length in range(min_len, max_len + 1):
        for i in range(len(whole_lines) - length + 1):
            chunk = "".join(whole_lines[i : i + length])
            ratio = SequenceMatcher(None, chunk, old).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_start = i
                best_end = i + length

    if best_ratio < similarity_threshold:
        return content, 0

    replace_lines = new.splitlines(keepends=True)
    updated = "".join(whole_lines[:best_start] + replace_lines + whole_lines[best_end:])
    return updated, 1


def apply_edit_with_fallback(
    content: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> tuple[str, int]:
    if old_string == "":
        return new_string, 1

    if replace_all:
        count = content.count(old_string)
        return content.replace(old_string, new_string), count

    exact_count = content.count(old_string)
    if exact_count == 1:
        return content.replace(old_string, new_string, 1), 1

    updated, count = _replace_whitespace_tolerant(content, old_string, new_string)
    if count > 0:
        return updated, count

    updated, count = _try_dotdotdots(content, old_string, new_string)
    if count > 0:
        return updated, count

    updated, count = _replace_fuzzy(content, old_string, new_string)
    if count > 0:
        return updated, count

    if exact_count > 1:
        return content, 0
    return content, 0
