FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

CMD ["celery", "-A", "app.celery_app.celery_app", "worker", "-Q", "orchestration", "--loglevel=INFO", "--concurrency=2"]

