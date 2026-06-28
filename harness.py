"""Entry point — wires up configuration and starts the agent loop."""

import os
import ollama
from terminal_io import _get_context_length
from tools import SYSTEM_PROMPT, AGENT_TOOLS
from agent_loop import run_loop


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

    run_loop(
        ollama_client=ollama_client,
        model_name=MODEL_NAME,
        system_prompt=SYSTEM_PROMPT,
        agent_tools=AGENT_TOOLS,
        context_length=context_length,
    )


if __name__ == "__main__":
    main()
