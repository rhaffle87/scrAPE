FROM python:3.11-slim

# Install system dependencies, Node.js, playwright, and create non-root user in a single layer
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && pip install --no-cache-dir playwright \
    && playwright install-deps chromium \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash appuser

WORKDIR /app

# Copy project files with appropriate ownership
COPY --chown=appuser:appuser pyproject.toml requirements.txt README.md ./
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser frontend/ ./frontend/
COPY --chown=appuser:appuser crawlee_bridge/ ./crawlee_bridge/
RUN mkdir -p data seeds && chown appuser:appuser data seeds
COPY --chown=appuser:appuser .bandit ./.bandit

# Install Python project dependencies and Node.js dependencies in a single layer
RUN pip install --no-cache-dir -e . \
    && cd crawlee_bridge \
    && npm install \
    && chown -R appuser:appuser /app/crawlee_bridge

# Switch to the non-root user
USER appuser

# Install Playwright browsers under the user's home directory
RUN playwright install chromium

# The default port used by scrAPE dashboard
EXPOSE 10001

# Start the dashboard using uvicorn binding to 0.0.0.0
CMD ["python", "-m", "uvicorn", "frontend.app:app", "--host", "0.0.0.0", "--port", "10001", "--log-level", "warning"]