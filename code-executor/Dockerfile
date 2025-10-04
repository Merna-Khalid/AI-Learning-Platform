FROM python:3.11-slim

# Install compilers and language runtimes
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    openjdk-21-jdk-headless \
    nodejs \
    npm \
    golang-go \
    rustc \
    cargo \
    firejail \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for running code safely
RUN useradd -m -s /bin/bash executor

# App setup
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Secure execution environment
RUN mkdir -p /tmp/executions && chown executor:executor /tmp/executions

USER executor
EXPOSE 8080
CMD ["python", "app.py"]
