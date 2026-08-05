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

# Install Python project into an isolated prefix we can copy cleanly later
RUN pip install --no-cache-dir --prefix=/install .

RUN cd crawlee_bridge \
    && PUPPETEER_SKIP_DOWNLOAD=true npm ci --omit=dev \
    && npm cache clean --force

# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && useradd -m -s /bin/bash appuser \
    && apt-get purge -y curl gnupg \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# System-wide installed packages stay root-owned (non-root can read/execute, not write)
COPY --from=builder /install /usr/local

# App code: root-owned, read-only for appuser
COPY --from=builder --chown=root:root /app/crawlee_bridge ./crawlee_bridge
COPY --chown=root:root frontend/ ./frontend/
COPY --chown=root:root .bandit ./.bandit

# Only runtime-writable dirs get appuser ownership
RUN mkdir -p data seeds && chown appuser:appuser data seeds

USER appuser

# Playwright + Chromium headless-shell, installed into appuser's own cache dir
RUN pip install --no-cache-dir playwright \
    && python -m playwright install --with-deps --only-shell chromium

EXPOSE 10001

CMD ["python", "-m", "uvicorn", "frontend.app:app", "--host", "0.0.0.0", "--port", "10001", "--log-level", "warning"]