FROM python:3.12-slim

ARG PROJECT_NAME=bench-python-project

# ---- System deps ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ---- Install uv ----
RUN pip install --no-cache-dir uv

WORKDIR /app

# ---- Copy project ----
COPY ./$PROJECT_NAME/pyproject.toml .
COPY ./$PROJECT_NAME/src ./src

# ---- Install Python deps ----
RUN uv pip install --system . 

# ---- Default command ----
CMD ["python3", "/app/src/scripts/monte_carlo.py"]