# ---------- Stage 1: Builder ----------
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml requirements.txt README.md ./
COPY src/ ./src/
COPY crawlee_bridge/ ./crawlee_bridge/

# Install Python project into an isolated prefix
RUN pip install --no-cache-dir --prefix=/install .

# Install Crawlee bridge dependencies
RUN cd crawlee_bridge \
    && PUPPETEER_SKIP_DOWNLOAD=true npm ci --omit=dev \
    && npm cache clean --force

# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

# Install system dependencies, Node.js 20, and Chromium browser
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    chromium \
    fonts-liberation \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && useradd -m -s /bin/bash appuser \
    && apt-get purge -y curl gnupg \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Point Puppeteer to system Chromium
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PYTHONPATH=/app:/app/src:/usr/local/lib/python3.11/site-packages/src

# System-wide installed Python packages
COPY --from=builder /install /usr/local

# App code: root-owned, read-only for appuser
COPY --from=builder --chown=root:root /app/crawlee_bridge ./crawlee_bridge
COPY --chown=root:root frontend/ ./frontend/
COPY --chown=root:root src/ ./src/
COPY --chown=root:root data/ ./data/
COPY --chown=root:root seeds/ ./seeds/
COPY --chown=root:root pyproject.toml ./pyproject.toml
COPY --chown=root:root .bandit ./.bandit

# Runtime-writable dirs setup (owned by appuser)
RUN mkdir -p data seeds logs output .cache && chown -R appuser:appuser data seeds logs output .cache

USER appuser

EXPOSE 10001

CMD ["python", "-m", "uvicorn", "frontend.app:app", "--host", "0.0.0.0", "--port", "10001", "--log-level", "warning"]