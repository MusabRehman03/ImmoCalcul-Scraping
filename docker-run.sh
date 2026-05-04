#!/bin/bash

# Docker run script for ImmoCalcul Scraper (without Docker Compose)

set -e

echo "Building Docker image..."
docker build -t immocalcul-scraper .

echo "Running scraper in Docker with virtual display..."

# Load environment variables from .env file
if [ -f .env ]; then
  # Source .env file with proper quote handling
  set -a
  source .env
  set +a
  echo "Loaded environment variables from .env"
fi

# Run docker - override ENTRYPOINT with --entrypoint
docker run -it \
  --entrypoint bash \
  -v "$(pwd):/app" \
  -v "$(pwd)/logs:/app/logs" \
  -e IMMOCALCUL_EMAIL="${IMMOCALCUL_EMAIL}" \
  -e IMMOCALCUL_PASSWORD="${IMMOCALCUL_PASSWORD}" \
  -e PARENT_DRIVE_FOLDER_ID="${PARENT_DRIVE_FOLDER_ID}" \
  -e PROXY_HOST="${PROXY_HOST}" \
  -e PROXY_PORT="${PROXY_PORT}" \
  -e PROXY_USER="${PROXY_USER}" \
  -e PROXY_PASS="${PROXY_PASS}" \
  -e DISPLAY=:99 \
  immocalcul-scraper -c "Xvfb :99 -screen 0 1366x768x24 > /dev/null 2>&1 & sleep 2 && python3 /app/sheet_processor.py $*"
