FROM python:3.11-slim

WORKDIR /app
COPY app.py /app/app.py

RUN pip install fastapi uvicorn httpx prometheus_client

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]