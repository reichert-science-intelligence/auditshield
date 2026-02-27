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

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Expose port (HuggingFace typically uses 7860)
EXPOSE 7860

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STARTUP_TIMEOUT=300

# Run app_complete.py which handles auto-initialization and PORT env var
CMD ["python", "app_complete.py"]
