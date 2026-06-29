"""Entry point — wires up configuration and starts the agent loop."""

import os
from pathlib import Path
import ollama
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


def _get_context_length(client, model_name: str) -> int:
    """Fetch the model's context length from Ollama's show endpoint.

    Ollama stores this as a dotted key in *model_info*, e.g.
    ``"tokenizer.ggml.context-length"``.  We walk every entry (including
    nested dicts) to find it regardless of depth or exact prefix.
    """
    try:
        info = client.show(model_name)
        mi = info.get('model_info', {}) or {}

        if 'context_length' in mi:
            return int(mi['context_length'])

        def _search(obj):
            """Recursively search *obj* for a context-length value."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if 'context' in str(k).lower() and 'length' in str(k).lower():
                        try:
                            return int(v)
                        except (ValueError, TypeError):
                            continue
                    result = _search(v)
                    if result > 0:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = _search(item)
                    if result > 0:
                        return result
            return 0

        return _search(mi) or 0
    except Exception:
        return 0


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
