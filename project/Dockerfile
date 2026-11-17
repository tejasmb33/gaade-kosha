FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 GAADE_DATA_DIR=/tmp/gaade
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt backend/requirements-cloud.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements-cloud.txt
COPY backend ./backend
COPY scripts ./scripts
COPY deployment ./deployment
CMD ["sh", "-c", "python scripts/bootstrap_cloud.py && exec uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers"]
