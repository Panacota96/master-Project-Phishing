FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py run.py lambda_handler.py seed_dynamodb.py setup_local_db.py ./
COPY app/ app/
COPY examples/ examples/

# Create non-root user for the app container
RUN useradd --create-home flask \
    && chown -R flask:flask /app

USER flask

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "run:app"]
