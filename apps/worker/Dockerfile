#worker/Dockerfile
FROM python:3.12-slim

WORKDIR /worker

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /worker/requirements.txt
RUN pip install --no-cache-dir -r /worker/requirements.txt

# Copy source code
COPY src /worker/src