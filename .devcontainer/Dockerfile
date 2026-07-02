# Use a verified base image with Node.js and Git pre-installed
FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm

# Install extra system utilities your coding agent might need to use 
# (e.g., build tools for compiling dependencies, curl, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv and sync project deps from pyproject.toml
RUN pip3 --disable-pip-version-check --no-cache-dir install \
        --upgrade pip setuptools wheel curl-cffi && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="$HOME/.local/bin:$PATH" && \
    uv sync --extra dev 2>&1 || true
