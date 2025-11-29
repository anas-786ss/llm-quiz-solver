dockerfile
FROM python:3.11-slim

# install dependencies for playwright
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates curl gcc libnss3 libatk1.0-0 libgtk-3-0 libx11-xcb1 libxcomposite1 libxrandr2 libxdamage1 libgbm1 libcups2 libxkbcommon0 libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# install playwright browsers
RUN playwright install --with-deps

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
