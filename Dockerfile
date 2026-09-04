# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_SYSTEM_PYTHON=1 UV_COMPILE_BYTECODE=1
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

# Install uv (Astral)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Python deps — uv-only (pyproject.toml + uv.lock)
COPY pyproject.toml uv.lock* .python-version* ./
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Node for Tailwind CLI (optional, prebuild CSS if present)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y nodejs \
 && rm -rf /var/lib/apt/lists/*

COPY . .

# Collect static (uses uv run to ensure venv)
RUN uv run python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000
CMD ["uv", "run", "gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60"]
