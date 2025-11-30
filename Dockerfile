# Hugging Face official Python image
FROM python:3.11

# Install OS dependencies required for Playwright on Spaces
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

# Install Playwright and Browsers
RUN pip install playwright && \
    playwright install chromium

# Create working directory
WORKDIR /app

# Copy dependency list
COPY requirements.txt .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Expose HF default port
EXPOSE 7860

# Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
