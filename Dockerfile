FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p recordings temp

# Expose the port HuggingFace Spaces expects
EXPOSE 7860

# Set environment variables (Spaces sets $PORT automatically)
ENV PYTHONPATH=/app

# Health check (optional, can be removed if Spaces doesn't use it)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/docs || exit 1

# Run the application on the port provided by Railway
   CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"] 