#!/usr/bin/env python3
"""Find all references to a Python symbol (function, class, method, or variable).

Uses Python's `ast` module so matches are based on real syntax rather than
naive text search. Both the definition sites and every use site are reported.

Usage:
    python find_references.py <symbol> [--root DIR] [--include-private]
    python find_references.py MyClass
    python find_references.py do_work --root src/pkg
    python find_references.py _helper --include-private

Prints lines of the form:  path/to/file.py:LINE  KIND  context
where KIND is one of: def, class, call, attr, name.
"""
from __future__ import annotations

import argparse
import ast
import os
import sys
from pathlib import Path


def _iter_py_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip common non-source directories.
        dirnames[:] = [
            d
            for d in dirnames
            if d not in {".git", "__pycache__", ".mypy_cache", ".venv", "venv", ".pytest_cache", "node_modules"}
        ]
        for fn in filenames:
            if fn.endswith(".py"):
                yield Path(dirpath) / fn


class ReferenceFinder(ast.NodeVisitor):
    def __init__(self, symbol: str, include_private: bool):
        self.symbol = symbol
        self.include_private = include_private
        self.results: list[tuple[int, str, str]] = []
        self.scope: list[str] = []

    def _in_scope(self) -> str:
        return ".".join(self.scope)

    def _record(self, node: ast.AST, kind: str, label: str) -> None:
        self.results.append((node.lineno, kind, label))

    def _matches(self, name: str) -> bool:
        if not self.include_private and name.startswith("_"):
            return False
        return name == self.symbol

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self._matches(node.name):
            self._record(node, "class", f"class {node.name}")
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node) -> None:
        if self._matches(node.name):
            self._record(node, "def", f"def {node.name}()")
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name) and self._matches(func.id):
            self._record(node, "call", f"call {func.id}() in {self._in_scope() or '<module>'}")
        elif isinstance(func, ast.Attribute) and self._matches(func.attr):
            self._record(node, "call", f"call .{func.attr}() in {self._in_scope() or '<module>'}")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if self._matches(node.attr) and not isinstance(node.ctx, ast.Store):
            self._record(node, "attr", f".{node.attr} in {self._in_scope() or '<module>'}")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if self._matches(node.id):
            kind = "name" if isinstance(node.ctx, ast.Load) else "assign"
            self._record(node, kind, f"{node.id} ({kind}) in {self._in_scope() or '<module>'}")
        self.generic_visit(node)


def find_references(symbol: str, root: Path, include_private: bool) -> int:
    total = 0
    for path in sorted(_iter_py_files(root)):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            print(f"! skip {path}: {exc}", file=sys.stderr)
            continue
        finder = ReferenceFinder(symbol, include_private)
        finder.visit(tree)
        for lineno, kind, label in sorted(finder.results):
            total += 1
            rel = path.relative_to(root) if path.is_relative_to(root) else path
            print(f"{rel}:{lineno}  {kind:<6} {label}")
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Find all references to a Python symbol.")
    parser.add_argument("symbol", help="Name of the function, class, method, or variable.")
    parser.add_argument("--root", default=".", help="Directory to search (default: current dir).")
    parser.add_argument("--include-private", action="store_true",
                        help="Also match symbols starting with an underscore.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"error: root path does not exist: {root}", file=sys.stderr)
        return 2

    count = find_references(args.symbol, root, args.include_private)
    print(f"\n{count} reference(s) to '{args.symbol}' under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
