FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application code first
COPY . .

# Install Python dependencies with compatible versions
RUN pip install -e . && \
    pip install -U "langgraph-cli[inmem]" && \
    pip install "pydantic>=2.0.0,<3.0.0"

# Expose the port that LangGraph dev server runs on
EXPOSE 8123

# Run the LangGraph server
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8123", "--allow-blocking", "--no-browser"]