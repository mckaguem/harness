#!/usr/bin/env python3
"""Print the source of a function, method, or class definition.

Locates the definition by name using Python's `ast` module and prints the
exact source lines (with line numbers) from the original file, so the output
is faithful byte-for-byte. Works on module-level and nested definitions.

Usage:
    python show_definition.py <symbol> [--root DIR] [--file PATH]
    python show_definition.py MyClass
    python show_definition.py do_work --file src/pkg/tasks.py
    python show_definition.py _helper --root src --include-private

If multiple definitions match, all are printed (separated by a divider).
"""
from __future__ import annotations

import argparse
import ast
import os
import sys
from pathlib import Path


def _iter_py_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in {".git", "__pycache__", ".mypy_cache", ".venv", "venv", ".pytest_cache", "node_modules"}
        ]
        for fn in filenames:
            if fn.endswith(".py"):
                yield Path(dirpath) / fn


class DefCollector(ast.NodeVisitor):
    def __init__(self, symbol: str, include_private: bool):
        self.symbol = symbol
        self.include_private = include_private
        self.matches: list[tuple[str, ast.AST]] = []

    def _try(self, node: ast.AST, name: str) -> None:
        if self.include_private or not name.startswith("_"):
            if name == self.symbol:
                self.matches.append((name, node))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._try(node, node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._try(node, node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._try(node, node.name)
        self.generic_visit(node)


def _print_source(file_path: Path, node: ast.AST) -> None:
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"! cannot read {file_path}: {exc}", file=sys.stderr)
        return
    start = node.lineno - 1
    end = getattr(node, "end_lineno", node.lineno)
    print(f"### {file_path}:{node.lineno}-{end}")
    width = len(str(end))
    for i in range(start, end):
        print(f"{i + 1:>{width}} | {lines[i]}")
    print()


def show_definition(symbol: str, root: Path, file_hint: Path | None, include_private: bool) -> int:
    found = 0
    if file_hint is not None:
        candidates = [file_hint.resolve()]
    else:
        candidates = list(_iter_py_files(root))

    for path in sorted(candidates):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            if file_hint is not None:
                print(f"! skip {path}: {exc}", file=sys.stderr)
            continue
        collector = DefCollector(symbol, include_private)
        collector.visit(tree)
        for _name, node in collector.matches:
            found += 1
            _print_source(path, node)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Show a Python definition's source.")
    parser.add_argument("symbol", help="Name of the function, method, or class.")
    parser.add_argument("--root", default=".", help="Directory to search (default: current dir).")
    parser.add_argument("--file", default=None, help="Restrict search to a single file.")
    parser.add_argument("--include-private", action="store_true",
                        help="Also match symbols starting with an underscore.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    file_hint = Path(args.file).resolve() if args.file else None

    if file_hint is not None and not file_hint.exists():
        print(f"error: file does not exist: {file_hint}", file=sys.stderr)
        return 2
    if file_hint is None and not root.exists():
        print(f"error: root path does not exist: {root}", file=sys.stderr)
        return 2

    found = show_definition(args.symbol, root, file_hint, args.include_private)
    if found == 0:
        print(f"No definition named '{args.symbol}' found.")
        return 1
    print(f"{found} definition(s) of '{args.symbol}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
