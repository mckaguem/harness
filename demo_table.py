"""Demo: exercise the terminal_io markdown renderer with a rich sample."""

from terminal_io.markdown.helpers import display_agent_response


SAMPLE = """## Demo Markdown Render

Here's some **bold text**, *italic text*, and `inline code` to test inline formatting.

You can also do ***bold-italics*** for emphasis.

### Sample Table

| Feature | Status | Notes |
|---------|--------|-------|
| Bold    | ✅     | Uses BOLD ANSI |
| Italics | ✅     | Uses DIM ANSI |
| Inline code | ✅ | Blue + bold |
| Tables  | ✅     | Box-drawing chars |

### Another Table — Right Aligned

| Item | Qty | Price |
|-----:|----:|------:|
| Apples | 5 | $2.50 |
| Bananas | 3 | $1.20 |
| Cherries | 10 | $8.00 |

### Code Block Demo

```python
def greet(name):
    # Return a greeting
    return "Hello, " + name + "!"

print(greet("world"))
```

Here's some *normal prose* mixed with `code` and **strong text** in the same paragraph. Lists work too — bullet points, numbered items, all the usual stuff.

That wraps up the demo! 🎉
"""


if __name__ == "__main__":
    # Simulate a minimal response dict so display_agent_response doesn't choke.
    dummy_response = {
        "done": True,
        "total_duration": 1_000_000_000,
        "eval_count": 50,
        "prompt_eval_count": 200,
    }
    display_agent_response(SAMPLE, dummy_response, context_length=4096)
