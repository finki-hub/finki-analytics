FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS builder

ENV UV_CREATE_VENV=1 \
    UV_VENV_PATH=/app/.venv \
    UV_PYTHON_MINOR=13 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.13-bookworm AS final

WORKDIR /app

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=3s CMD wget --quiet --tries=1 --spider http://127.0.0.1:8088/health/ || exit 1

EXPOSE 8088

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]
