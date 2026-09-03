FROM python:3.12-slim

WORKDIR /srv
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /srv/backend/requirements.txt
RUN pip install --no-cache-dir -r /srv/backend/requirements.txt

COPY backend /srv/backend
COPY data /srv/data

WORKDIR /srv/backend
ENV PYTHONPATH=/srv/backend
ENV DATA_DIR=/srv/data
ENV STORAGE_DIR=/srv/data/storage

EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
