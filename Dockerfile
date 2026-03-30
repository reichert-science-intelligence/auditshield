# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Supabase stack first (install order matters for HF Spaces)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
    gotrue==1.3.0 \
    httpcore==0.16.3 \
    httpx==0.23.3 \
    anyio==3.7.1 \
    python-dotenv==1.0.0 \
    supabase==2.3.0 \
    && pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Expose port (HuggingFace typically uses 7860)
EXPOSE 7860

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STARTUP_TIMEOUT=300
# HuggingFace /app is read-only - use /tmp for SQLite
ENV SQLITE_PATH=/tmp/auditshield.db

# Run app_complete.py which handles auto-initialization and PORT env var
CMD ["python", "app_complete.py"]
