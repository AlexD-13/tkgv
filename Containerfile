# syntax=docker/dockerfile:1
# Multistage container image for GestionPlatos (Podman/Docker compatible, rootless-friendly).

# ---------- Stage 1: build the Nuxt frontend ----------
FROM oven/bun:1 AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/bun.lock ./
RUN bun install --frozen-lockfile

COPY frontend/ ./

ARG NUXT_PUBLIC_API_BASE=http://localhost:8000/api
ARG NUXT_PUBLIC_SITE_URL=
ENV NUXT_PUBLIC_API_BASE=${NUXT_PUBLIC_API_BASE}
ENV NUXT_PUBLIC_SITE_URL=${NUXT_PUBLIC_SITE_URL}

RUN bunx --bun nuxt generate

# ---------- Stage 2: prepare the FastAPI backend environment ----------
FROM python:3.13-slim AS backend-builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app/backend

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-package backend

COPY backend/ ./

# ---------- Stage 3: final runtime image ----------
FROM python:3.13-slim AS runtime

WORKDIR /app/backend

RUN groupadd --system app && useradd --system --gid app --home-dir /app/backend app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY --from=backend-builder /app/backend /app/backend

COPY --from=frontend-builder /app/frontend/.output/public /app/backend/public

RUN chmod +x /app/backend/entrypoint.sh \
 && chown -R app:app /app/backend

USER app

ENV PATH="/app/backend/.venv/bin:/usr/local/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/status')" || exit 1

ENTRYPOINT ["/app/backend/entrypoint.sh"]