# ---------- Build stage ----------
FROM python:3.12-slim AS builder

ARG PROJECT_NAME=bench-python-project
ARG TEMPORAL_CODE_PROJECT=temporal-code
ARG WORKER_SCRIPT=/app/temporal-worker/src/run_worker.py

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"
    
WORKDIR /build

# Copy benchmark package
COPY ./$PROJECT_NAME ./python-benchmark
COPY ./$TEMPORAL_CODE_PROJECT ./temporal-worker

# Install both packages into a target directory
RUN uv pip install --no-cache-dir \
    ./python-benchmark \
    ./temporal-worker \
    --target /opt/python
    
# ---------- Runtime stage ----------
FROM python:3.12-slim AS runtime

ARG PROJECT_NAME=bench-python-project
ARG TEMPORAL_CODE_PROJECT=temporal-code

WORKDIR /app

# Copy installed packages
COPY --from=builder /opt/python /opt/python

ENV PYTHONPATH="/opt/python"

COPY ./$PROJECT_NAME/src ./python-benchmark/src
COPY ./$TEMPORAL_CODE_PROJECT/src ./temporal-worker/src

# Run the Temporal worker
ENTRYPOINT ["python3", $WORKER_SCRIPT]