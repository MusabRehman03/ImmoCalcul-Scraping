FROM python:3.9-slim

# Install system dependencies including Xvfb, display utilities, and Chromium dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    x11-utils \
    wget \
    git \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libasound2 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libx11-6 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and Chromium
RUN python -m playwright install chromium

# Copy the entire project
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default to bash if no args provided
CMD ["bash"]
