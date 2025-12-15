FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxinerama1 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libasound2 \
    libpulse0 \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY price_tracker.py ./

# Install Python dependencies
RUN uv sync --frozen

# Install Playwright browsers
RUN uv run playwright install

# Copy config (will be overridden by volume)
COPY config.example.json ./config.example.json

# Create data directory
RUN mkdir -p /app/data

ENTRYPOINT ["uv", "run", "price_tracker.py"]
