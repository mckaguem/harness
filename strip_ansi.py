"""Run demo_table.py, capture output, strip ANSI codes, print clean view."""
import io, sys, re, contextlib


def strip(s):
    return re.sub(r'\033\[[^m]*m', '', s)


buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
    from demo_table import SAMPLE
    dummy_response = {
        "done": True,
        "total_duration": 1_000_000_000,
        "eval_count": 50,
        "prompt_eval_count": 200,
    }
    from terminal_io.markdown.helpers import display_agent_response
    display_agent_response(SAMPLE, dummy_response, context_length=4096)

for line in buf.getvalue().splitlines():
    print(strip(line))
