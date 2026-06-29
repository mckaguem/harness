# Use a verified base image with Node.js and Git pre-installed
FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm

# Install extra system utilities your coding agent might need to use 
# (e.g., build tools for compiling dependencies, curl, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp
