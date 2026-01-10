# =========================
# Builder stage
# =========================
FROM python:3.12-slim AS builder

ARG PROJECT_NAME=bench-python-project

WORKDIR /build

# System deps kept minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency metadata first (better caching)
COPY ${PROJECT_NAME}/pyproject.toml .
COPY ${PROJECT_NAME}/src ./src

# Create a virtualenv to copy into runtime
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install .

# =========================
# Runtime stage
# =========================
FROM apache/airflow:3.0.2-python3.12 AS runtime

ARG PROJECT_NAME=bench-python-project

USER root

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

COPY ./$PROJECT_NAME/src/scripts /opt/airflow/scripts

# Ensure airflow uses our venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/opt/venv/lib/python3.12/site-packages:$PYTHONPATH"

# Avoid pip install at runtime
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=True

USER airflow