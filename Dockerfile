FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libfreetype6 \
    libfreetype6-dev \
    libpng-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

# Copy application code
COPY . .

RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir -U "langgraph-cli[inmem]" && \
    pip install --no-cache-dir "pydantic>=2.0.0,<3.0.0"

# Expose the port that LangGraph dev server runs on
EXPOSE 8123

# Run the LangGraph server
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8123", "--allow-blocking", "--no-browser"]
