# Use a verified base image with Node.js and Git pre-installed
FROM mcr.microsoft.com/devcontainers/javascript-node:24

# Install extra system utilities your coding agent might need to use 
# (e.g., build tools for compiling dependencies, curl, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Nanocoder globally inside the sandbox environment
RUN npm install -g @nanocollective/nanocoder