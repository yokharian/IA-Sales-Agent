# Base Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create necessary directories
RUN mkdir -p data/chroma data/documents logs

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Create a startup script that runs CSV ingestion first, then starts the WhatsApp server
RUN set -e; \
    cat > /app/start.sh <<'EOF' && chmod +x /app/start.sh
#!/usr/bin/env sh
set -e

echo "🚀 Starting Commercial Agent Setup..."
echo "📊 Step 1: Running CSV ingestion..."
cd /app
python scripts/ingest_csv.py data/sample_vehicles.csv --create-tables

echo "✅ CSV ingestion completed successfully"
echo "📱 Step 2: Starting WhatsApp server..."
exec python src/whatsapp_server.py --host 0.0.0.0 --port 5000
EOF

# Expose the port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the startup script
CMD ["/app/start.sh"]
