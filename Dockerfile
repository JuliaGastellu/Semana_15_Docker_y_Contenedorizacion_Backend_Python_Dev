FROM ghcr.io/astral-sh/uv:0.9.5 AS uv
FROM python:3.12-slim AS builder
COPY --from=uv /uv /bin/uv
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --python /usr/local/bin/python
COPY app app
COPY migrations migrations
COPY alembic.ini entrypoint.sh ./

FROM python:3.12-slim AS runtime
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
COPY --from=builder --chown=appuser:appuser /app /app
RUN chmod +x entrypoint.sh && mkdir -p var/uploads && chown -R appuser:appuser var
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
ENTRYPOINT ["./entrypoint.sh"]

FROM builder AS test
ENV PATH="/app/.venv/bin:$PATH"
RUN uv sync --frozen --python /usr/local/bin/python
COPY tests tests
ENTRYPOINT []
CMD ["/app/.venv/bin/python", "-m", "pytest", "--cov", "--cov-report=term-missing", "--cov-report=xml:/reports/coverage.xml", "-q"]
