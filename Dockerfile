FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir pyrogram tgcrypto
CMD ["python3", "main.py"]
