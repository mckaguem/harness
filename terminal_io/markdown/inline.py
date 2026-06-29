"""Inline markdown transforms — bold, italic, code."""


import re

from ..colors import BOLD, DIM, RESET, BLUE


# ANSI helpers for inline markdown.
def _md_italics(m):
    return f"{DIM}{m.group(1)}{RESET}"


def _md_bold(m):
    return f"{BOLD}{m.group(1)}{RESET}"


def _md_bold_italics(m):
    return f"{BOLD}{DIM}{m.group(1)}{RESET}"


def _md_code_inline(m):
    inner = m.group(1) or ''
    return f"{BOLD}{BLUE}{inner}{RESET}"


# Ordered longest-first so ``***bold-italics***`` beats ``**bold**``.
_MD_INLINES: list[tuple[str, re.Pattern]] = [
    ('code',     re.compile(r'(?<!\\)`([^`]+?)`')),  # `code`
    ('b-i',      re.compile(r'\*{3}(.+?)\*{3}', re.DOTALL)),
    ('bold',     re.compile(r'\*{2}(.+?)\*{2}', re.DOTALL)),
    ('italic',   re.compile(r'(?<!\*)\*(?![*])(.+?)(?<!\*)\*(?!\*)')),  # single *
]


def _md_inline(text: str) -> str:
    """Apply inline markdown transforms to *text*."""
    out = text.strip()
    if not out:
        return ''
    for name, pat in _MD_INLINES:
        if name == 'code':
            out = pat.sub(_md_code_inline, out)
        elif name == 'b-i':
            out = pat.sub(_md_bold_italics, out)
        elif name == 'bold':
            out = pat.sub(_md_bold, out)
        else:
            out = pat.sub(_md_italics, out)
    return out
