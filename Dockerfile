# WeirdClauses Public Mock Demo Dockerfile
# Slim build without PyTorch or GPU libraries
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WC_MOCK=1 \
    WC_PUBLIC_DEMO=1 \
    PORT=8000

WORKDIR /app

# Install lightweight dependencies
COPY requirements-demo.txt .
RUN pip install --no-cache-dir -r requirements-demo.txt

# Copy package metadata and source code
COPY pyproject.toml .
COPY weirdclauses/ weirdclauses/
COPY baseline_packs/ baseline_packs/
COPY samples/ samples/
COPY docs/ docs/

# Install weirdclauses package without downloading heavy dependencies
RUN pip install --no-cache-dir --no-deps -e .

EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + str('${PORT:-8000}') + '/health')" || exit 1

# Start the mock demo web server
CMD ["sh", "-c", "weirdclauses serve --host 0.0.0.0 --port ${PORT:-8000} --mock"]
