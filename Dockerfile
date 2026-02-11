FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py run.py seed.py ./
COPY app/ app/
COPY examples/ examples/

# Create non-root user and data directory for SQLite
RUN useradd --create-home flask \
    && mkdir -p /data \
    && chown -R flask:flask /app /data

USER flask

# SQLite database lives on a Docker volume mounted at /data
ENV DATABASE_URL=sqlite:////data/app.db

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "run:app"]
