# Base Python image
FROM python:3.11

# Install system dependencies required for Chromium
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 🔥 Install Playwright first
RUN pip install --upgrade pip \
    && pip install playwright

# 🔥 FORCE INSTALL Chromium browser (Render was skipping this step)
RUN playwright install chromium

# Work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install app dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose Render port
EXPOSE 7860

# Run FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
