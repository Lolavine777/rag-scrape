# Stage 1: Build virtual environment with dependencies
FROM python:3.12-slim-bookworm AS builder

# Install uv
COPY --from=astralsh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy only dependency definitions to leverage cache
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Stage 2: Runtime image
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv
COPY src /app/src
COPY main.py /app/main.py

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set default entrypoint
ENTRYPOINT ["python", "main.py"]
