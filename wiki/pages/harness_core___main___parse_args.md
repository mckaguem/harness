---
name: "harness_core.__main__.parse_args"
description: "Parse CLI arguments with :mod:`getopt`."
source: "harness_core/__main__.py"
---

Parse CLI arguments with :mod:`getopt`.

Args:
    argv: A list of argument strings (typically ``sys.argv[1:]``).

Returns:
    dict: ``{"message": str | None, "help": bool}``. ``message`` is the
    value of ``--message``/``-m`` (or ``None`` when the flag is absent).

Exits:
    Calls ``sys.exit(2)`` on an unknown option or a missing required
    argument, printing usage to stderr first.

## Signature
```python
parse_args(argv)
```

## References
- [Module: harness_core.__main__](harness_core___main__) - Parent module
