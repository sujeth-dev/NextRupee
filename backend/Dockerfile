FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN pip install .

EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=10s --start-period=15s \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=8).raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
