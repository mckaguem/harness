"""High-level markdown rendering helpers — orchestrates inline transforms and block renderers."""


import os
import re

from .inline import _md_inline
from ..colors import BOLD, RESET, DIM


MAX_DISPLAY_LINES = 5


def display_agent_response(content: str, response: dict, context_length: int,
                           prompt_token_count: int | None = None) -> None:
    """Print the agent's text response along with token-speed stats.

    *content* is interpreted as markdown and rendered into styled ANSI before
    being displayed inside a box.  Fenced code blocks and tables get their own
    boxes; prose paragraphs, headings, and lists are wrapped together in one.
    """
    from .blocks import _render_table, _render_code_block
    from ..speed import _format_speed

    try:
        width = os.get_terminal_size().columns
    except (OSError, AttributeError):
        width = 80
    sections: list[str] = []
    current_block: list[str] = []
    i = 0
    lines_in = content.split('\n')

    # Phase-1 pass: split the raw markdown into prose, code blocks and tables.
    while i < len(lines_in):
        line = lines_in[i]
        stripped = line.strip()

        # Fenced code block — grab until closing `````.
        if stripped.startswith('```'):
            lang_match = re.search(r'```(\w*)', stripped)
            lang = lang_match.group(1) if lang_match else ''
            code_lines: list[str] = []
            i += 1
            while i < len(lines_in) and not lines_in[i].strip().startswith('```'):
                code_lines.append(lines_in[i])
                i += 1
            i += 1  # skip closing fence
            sections.append(_render_code_block('\n'.join(code_lines), lang, width))
            continue

        # Table — if the next few lines look like a table.
        if stripped.startswith('|') and i + 2 < len(lines_in):
            tbl = []
            while i < len(lines_in) and lines_in[i].strip().startswith('|'):
                tbl.append(lines_in[i])
                i += 1
            rendered = _render_table(tbl, width)
            if rendered:
                sections.append(rendered)
            continue

        # Headings — render as bold prefix.
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if heading_match and not current_block:
            level = len(heading_match.group(1))
            text = _md_inline(heading_match.group(2)).strip()
            sections.append(f"{BOLD}{text}{' ' * (width - 4 - len(text) - max(level-1,0)*8)}")
            i += 1
            continue

        # Empty line — flush current block and start a new one.
        if not stripped:
            if current_block:
                sections.append('\n'.join(current_block))
                current_block = []
            i += 1
            continue

        # Prose/paragraph — accumulate lines until blank or structural marker.
        rendered_line = _md_inline(line)
        current_block.append(rendered_line)
        i += 1

    if current_block:
        sections.append('\n'.join(current_block))

    # Phase-2 pass: join prose blocks (with a blank line between them), but
    # always emit code blocks / tables as their own separated boxes.
    prose_parts: list[str] = []
    for sec in sections:
        sec_stripped = sec.strip()
        if not sec_stripped:
            continue
        # A section is "prose" when it contains NO box-border chars and no
        # leading/trailing box lines.
        if re.search(r'^\+[-]{3,}\+$', sec_stripped, re.MULTILINE) or \
           sec_stripped.startswith('+'):  # fenced code blocks start with +
            prose_parts.append(sec)
        else:
            prose_parts.append(sec.strip())

    full_text = '\n\n'.join(p for p in prose_parts if p)
    from ..boxes import print_box
    print_box("🤖 Agent Response", full_text, style="agent")
    speed_info = _format_speed(response, context_length, prompt_token_count)
    if speed_info:
        print(speed_info)
