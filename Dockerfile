FROM python:3.10-slim
# تثبيت ffmpeg و aria2 للتعامل مع روابط التورنت
RUN apt-get update && apt-get install -y ffmpeg aria2 && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir pyrogram tgcrypto flask
CMD ["python3", "main.py"]
