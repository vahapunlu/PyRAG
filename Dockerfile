# Use official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (build-essential for compiling some python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# Excluding GUI libs to save space/time and avoid display errors
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ ./src/
COPY data/ ./data/ 
# COPY qdrant_db/ ./qdrant_db/  <-- We use CLOUD DB, so no need to copy local DB
# COPY cache_db/ ./cache_db/    <-- Cache starts empty

# Make sure log directory exists
RUN mkdir -p logs

# Expose the API port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
