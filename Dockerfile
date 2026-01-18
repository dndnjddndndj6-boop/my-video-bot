FROM python:3.9-slim-buster

# تثبيت FFmpeg ومكتبة التورنت من مخازن النظام لضمان التوافق
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3-libtorrent \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ جميع الملفات إلى السيرفر
COPY . .

# تثبيت مكتبات البايثون الأخرى
RUN pip install --no-cache-dir -r requirements.txt

# أمر تشغيل البوت
CMD ["python3", "main.py"]

