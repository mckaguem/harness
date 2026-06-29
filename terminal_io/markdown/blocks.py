"""Block-level markdown renderers — tables and fenced code blocks."""

import re
import unicodedata
from collections import Counter

from ..colors import BOLD, RESET


def _cell_visible_width(cell: str) -> int:
    """Visible column width of *cell*, accounting for double-width Unicode (e.g. CJK, emoji)."""
    return sum(2 if unicodedata.east_asian_width(c) in ('F', 'W') else 1 for c in cell)


def _ljust_visible(s: str, total_visible_width: int) -> str:
    """Left-justify *s* to *total_visible_width* columns (considering double-width chars)."""
    if total_visible_width <= 0:
        return s
    w = _cell_visible_width(s)
    if w >= total_visible_width:
        return s[:total_visible_width]
    pad = ' ' * (total_visible_width - w)
    return s + pad


def _render_table(lines: list[str], width: int) -> str:
    """Render a markdown table into aligned ANSI columns with box-drawing characters."""
    # First pass: collect all rows and identify separator candidates.
    # Split on blank lines so back-to-back markdown tables don't merge into one.
    groups: list[list[str]] = []
    current_group: list[str] = []
    for ln in lines:
        stripped = ln.strip()
        if not stripped or not stripped.startswith('|'):
            if current_group:
                groups.append(current_group)
                current_group = []
            continue
        inner = stripped.strip('|').strip()
        cols = [c.strip() for c in inner.split('|')]
        current_group.append(cols)
    if current_group:
        groups.append(current_group)

    # Render each non-empty group as its own table, joined by blank lines.
    rendered_tables: list[str] = []
    for grp in groups:
        if not grp:
            continue

        # Identify separator rows: cells contain only -, :, and spaces (no |).
        separator_indices = set()
        for idx, row in enumerate(grp):
            test_str = ''.join(row).replace('-', '').replace(':', '').replace(' ', '')
            if not test_str:
                separator_indices.add(idx)

        # Get data rows (non-separator) and determine expected column count.
        data_rows = [row for idx, row in enumerate(grp) if idx not in separator_indices]
        if not data_rows:
            continue

        # Use the most common column count among data rows as expected.
        col_counts = Counter(len(r) for r in data_rows)
        expected_cols = col_counts.most_common(1)[0][0] if col_counts else 0

        num_cols = max(expected_cols, len(data_rows[0]))
        widths = [0] * num_cols

        # Calculate column visible-widths from all content (header + data).
        for row in data_rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], _cell_visible_width(cell))

        # Box-drawing characters
        HORIZONTAL = '─'
        VERTICAL = '│'
        TOP_LEFT = '┌'
        TOP_RIGHT = '┐'
        BOTTOM_LEFT = '└'
        BOTTOM_RIGHT = '┘'
        CROSS = '┼'
        T_DOWN = '┬'
        T_UP = '┴'

        parts: list[str] = []

        # Top border — each column gets (width + 2) horizontal chars.
        top_parts = [TOP_LEFT]
        for w in widths:
            top_parts.append(HORIZONTAL * (w + 2))
            top_parts.append(T_DOWN)
        top_parts[-1] = TOP_RIGHT
        parts.append(''.join(top_parts))

        # Header row
        header_row = data_rows[0]
        inner_cells = []
        for i in range(num_cols):
            cell = header_row[i] if i < len(header_row) else ''
            padded_cell = _ljust_visible(cell, widths[i])
            inner_cells.append(f' {padded_cell} ')
        parts.append(f"{VERTICAL}{VERTICAL.join(inner_cells)}{VERTICAL}")

        # Separator after header
        sep_parts = [CROSS]
        for w in widths:
            sep_parts.append(HORIZONTAL * (w + 2))
            sep_parts.append(CROSS)
        sep_parts[-1] = CROSS
        parts.append(''.join(sep_parts))

        # Data rows
        for row in data_rows[1:]:
            inner_cells = []
            for i in range(num_cols):
                cell = row[i] if i < len(row) else ''
                padded_cell = _ljust_visible(cell, widths[i])
                inner_cells.append(f' {padded_cell} ')
            parts.append(f"{VERTICAL}{VERTICAL.join(inner_cells)}{VERTICAL}")

        # Bottom border
        bottom_parts = [BOTTOM_LEFT]
        for w in widths:
            bottom_parts.append(HORIZONTAL * (w + 2))
            bottom_parts.append(T_UP)
        bottom_parts[-1] = BOTTOM_RIGHT
        parts.append(''.join(bottom_parts))

        rendered_tables.append('\n'.join(parts))

    return '\n\n'.join(rendered_tables)


def _render_code_block(block: str, lang: str, width: int) -> str:
    """Format a single `` ```...`` ` block as a monospaced box."""
    lines = block.split('\n')
    if not lines:
        return ''
    longest_plain = max(len(re.sub(r'\033\[[^m]*m', '', l)) for l in lines)
    # pad to 48 so the box looks consistent regardless of content width
    inner_width = min(max(longest_plain, 48), width - 2)
    border_top = '+-' + '-' * (inner_width) + '-+'
    border_bot = '+' + '-' * (inner_width) + '-+'
    title = f' {BOLD}{lang or "text"} ' if lang else None
    parts = [border_top]
    for line in lines:
        padded_line = line.ljust(inner_width)[:inner_width]
        parts.append(f'|{padded_line}|')
    parts.append(border_bot)

    # Prepend language label to output if present
    result = '\n'.join(parts)
    if title:
        return f"\n{title}\n{result}"
    return result
