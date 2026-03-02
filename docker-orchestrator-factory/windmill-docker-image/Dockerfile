# ---- Build stage ----


FROM ghcr.io/windmill-labs/windmill:main AS builder

ARG PROJECT_NAME=bench-python-project
ARG PYTHON_VERSION=3_11

# Installer dépendances de build
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl build-essential \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Copier le code du projet (adapter selon l'arborescence réelle)

COPY ./$PROJECT_NAME .

RUN uv pip compile pyproject.toml \
                        --python 3.11 \
                        -o requirements.lock

RUN echo requirements.lock

RUN uv pip install \
                --python 3.11 \
                --system . \
                -r requirements.lock \
                --target /tmp/windmill/cache/python_$PYTHON_VERSION/global-site-packages



# ---- Runtime stage ----


FROM ghcr.io/windmill-labs/windmill:main AS runtime

ARG PROJECT_NAME=bench-python-project
ARG PYTHON_VERSION=3_11

WORKDIR /app

COPY --from=builder /tmp/windmill/cache/python_$PYTHON_VERSION/global-site-packages /tmp/windmill/cache/python_$PYTHON_VERSION/global-site-packages

COPY ./$PROJECT_NAME/src/scripts /app/src/scripts

ENV PYTHONPATH="/tmp/windmill/cache/python_$PYTHON_VERSION/global-site-packages:\${PYTHONPATH}"

CMD ["windmill"]