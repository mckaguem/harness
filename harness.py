"""Entry point — wires up configuration and starts the agent loop."""

import os
from pathlib import Path
import ollama
from terminal_io import _get_context_length
from tools import AGENT_TOOLS
from agent_loop import run_loop


def build_system_prompt() -> str:
    """Read system_prompt.txt and inject a listing of the current directory.

    If an ``AGENTS.md`` file exists in the working directory its contents are
    appended so the agent can follow any project-specific conventions.
    """
    prompt_path = Path(__file__).parent / "system_prompt.txt"
    base = prompt_path.read_text(encoding="utf-8")

    # List files/dirs in the current working directory
    cwd_contents = "\n".join(
        entry.name for entry in sorted(Path.cwd().iterdir())
    )
    injection = (
        f"\n\nCurrent working directory contents:\n{cwd_contents}"
    )

    # Incorporate AGENTS.md if it exists.
    agents_md = Path.cwd() / "AGENTS.md"
    if agents_md.is_file():
        try:
            agents_content = agents_md.read_text(encoding="utf-8").strip()
            if agents_content:
                injection += (
                    f"\n\n--- AGENTS.md ---\n{agents_content}\n--- end AGENTS.md ---"
                )
        except Exception:
            pass

    return base + injection


def main():
    MODEL_NAME = 'hf.co/deepreinforce-ai/Ornith-1.0-35B-GGUF:Q6_K'

    ollama_host = os.environ.get(
        "OLLAMA_HOST",
        os.environ.get("OPENAI_BASE_URL", "http://localhost:11435"),
    )
    # strip trailing /v1 if the user passed an OpenAI-format URL — Ollama client needs bare base
    if ollama_host.rstrip("/").endswith("/v1"):
        ollama_host = ollama_host[: -len("/v1")]

    ollama_client = ollama.Client(host=ollama_host)
    context_length = _get_context_length(ollama_client, MODEL_NAME)

    system_prompt = build_system_prompt()

    run_loop(
        ollama_client=ollama_client,
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
        agent_tools=AGENT_TOOLS,
        context_length=context_length,
    )


if __name__ == "__main__":
    main()
