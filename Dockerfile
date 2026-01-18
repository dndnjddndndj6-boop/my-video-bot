# استخدام نسخة أحدث ومستقرة من بايثون
FROM python:3.10-slim-bullseye

# تحديث وتثبيت الأدوات (تغيير الإصدار يحل مشكلة 404)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3-libtorrent \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# تثبيت المكتبات مع تحديث pip لضمان عدم حدوث تعارض
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]
