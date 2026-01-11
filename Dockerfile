# Dockerfile for Railway (Docker deployment)
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py /app/bot.py

# Run as a worker (polling)
CMD ["python", "bot.py"]
