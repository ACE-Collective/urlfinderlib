# Use Python 3.10 base image
FROM mcr.microsoft.com/devcontainers/python:3.10-bullseye

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set up uv environment variables
ENV UV_LINK_MODE=copy

# Copy project files for dependency installation
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv (if lock file exists)
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then uv sync --frozen --dev; fi
