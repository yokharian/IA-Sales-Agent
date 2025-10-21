# Base Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python -m pip install --upgrade setuptools wheel

# Default command: run a simple smoke test
CMD ["python", "test.py"]

