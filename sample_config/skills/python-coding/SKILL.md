---
name: python-coding
description: Guidance and helper scripts for writing, reading, and verifying Python code. Use when working on Python modules, finding references to a function or class, reading a definition, deciding module structure, running mypy type checks, or creating and running pytest tests.
---

# Python Coding

Helper skill for day-to-day Python development in this codebase. It bundles
two executable scripts (for locating symbols and reading definitions) and
reference docs covering module structure, static type checking, and testing.

## When to use

- You need to find every reference to a function, class, method, or variable.
- You need to read a function/method/class definition with its exact source.
- You are structuring a new Python module or package.
- You need to run a static type checker (mypy) or write/run pytest tests.
- The task touches anything in `*.py` files.

## Scripts

Both scripts live in `scripts/` and use Python's `ast` module, so they match
on real syntax (not naive text search) and respect Python scoping.

### Find all references — `scripts/find_references.py`

Reports every definition and use site of a symbol, across a directory tree.

```bash
python skills/python_coding/scripts/find_references.py <symbol> [--root DIR] [--include-private]
python skills/python_coding/scripts/find_references.py Agent --root agent
python skills/python_coding/scripts/find_references.py do_work --include-private
```

Output format: `path:LINE  KIND  context`, where `KIND` is one of
`class`, `def`, `call`, `attr`, `name`, `assign`.

### Read a definition — `scripts/show_definition.py`

Prints the exact source lines (with line numbers) of a matching definition.

```bash
python skills/python_coding/scripts/show_definition.py <symbol> [--root DIR] [--file PATH] [--include-private]
python skills/python_coding/scripts/show_definition.py Agent --file agent/core.py
python skills/python_coding/scripts/show_definition.py _helper --root src
```

Use `--file` to scope to a single file for speed when you already know where
the symbol lives.

## Reference material

Load these only when the task needs the detail:

- `references/module_structure.md` — package layout, `__init__.py`
  discipline, import ordering, public/private conventions, error handling.
- `references/typechecking.md` — installing and configuring `mypy`, running
  it, handling third-party types, suppressing false positives, CI gating.
- `references/testing.md` — pytest layout, fixtures, `tmp_path`, mocking,
  running tests, and best practices.

## Workflow

1. Use `find_references.py` to understand a symbol's blast radius before
   changing it.
2. Use `show_definition.py` to read the exact implementation you must modify.
3. Make the change following the module-structure conventions.
4. Run `mypy` (see `references/typechecking.md`) to catch type regressions.
5. Add or update tests with `pytest` (see `references/testing.md`) and run
   them.
