FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ src/
COPY config.example.yaml /app/config.default.yaml
COPY scripts/entrypoint.sh /app/entrypoint.sh

ENV PYTHONPATH=/app/src

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --extra web --extra all-providers \
    && adduser --disabled-password --home /data/coach appuser \
    && mkdir -p /data/coach && chown appuser /data/coach \
    && chmod +x /app/entrypoint.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
