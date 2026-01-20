import os, threading, subprocess, time
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 1. تشغيل سيرفر وهمي لإبقاء البوت نشطاً على Render
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Running!"
def run_web_app():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_web_app, daemon=True).start()

# 2. إعدادات البوت
API_ID = 32370962
API_HASH = "8d41f5c8b0f5e4efa0a74e13a02e41f7"
BOT_TOKEN = "8304901124:AAHsFSAyhd5jQs_5zkZGbg4ZO97rYSSniwk"

app = Client("subtitle_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}

@app.on_message(filters.document)
async def handle_docs(client, message):
    if message.document.file_name.endswith(('.srt', '.ass')):
        user_data[message.from_user.id] = {'sub': await message.download()}
        await message.reply("✅ تم حفظ الترجمة بنجاح. أرسل الآن رابط Magnet أو رابط فيديو مباشر.")

@app.on_message(filters.text & (filters.regex(r'^http.*') | filters.regex(r'^magnet:.*')))
async def handle_link(client, message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return await message.reply("❌ من فضلك أرسل ملف الترجمة (.srt أو .ass) أولاً!")
    
    user_data[user_id]['url'] = message.text
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("1080p (الأصلية)", callback_data="1080")],
        [InlineKeyboardButton("720p (توفير مساحة)", callback_data="720")],
        [InlineKeyboardButton("480p (أصغر حجم)", callback_data="480")]
    ])
    await message.reply("رابط مكتشف! اختر الجودة المطلوبة (سيتم حذف الترجمات القديمة وحرق ترجمتك):", reply_markup=buttons)

@app.on_callback_query()
async def process_video(client, callback_query):
    user_id = callback_query.from_user.id
    quality = callback_query.data
    url = user_data[user_id]['url']
    sub_path = user_data[user_id]['sub']
    
    msg = await callback_query.message.edit(f"📥 جاري معالجة الجودة {quality}p... (قد تستغرق العملية وقتاً حسب حجم التورنت)")

    # إنشاء مجلد مؤقت للتحميل
    download_dir = f"dl_{user_id}_{int(time.time())}"
    os.makedirs(download_dir, exist_ok=True)
    
    try:
        # تحميل الملف
        if url.startswith("magnet:"):
            # تحميل التورنت باستخدام aria2
            subprocess.run(f'aria2c --follow-magnet=mem --seed-time=0 --max-overall-download-limit=0 "{url}" -d {download_dir}', shell=True, check=True)
        else:
            # تحميل رابط مباشر
            subprocess.run(f'wget "{url}" -P {download_dir}', shell=True, check=True)

        # البحث عن ملف الفيديو داخل المجلد (أكبر ملف)
        video_files = []
        for root, dirs, files in os.walk(download_dir):
            for file in files:
                if file.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                    video_files.append(os.path.join(root, file))
        
        if not video_files:
            return await msg.edit("❌ لم يتم العثور على ملف فيديو داخل الرابط.")
        
        input_video = max(video_files, key=os.path.getsize)
        output_video = f"final_{quality}p_{user_id}.mp4"

        # إعدادات الأبعاد
        scale = ""
        if quality == "720": scale = "scale=1280:-2,"
        elif quality == "480": scale = "scale=854:-2,"

        # أمر FFmpeg: -sn يحذف الترجمات القديمة، و -vf يحرق ترجمتك
        cmd = f'ffmpeg -i "{input_video}" -vf "{scale}subtitles={sub_path}" -sn -c:v libx264 -crf 26 -preset faster -c:a aac -b:a 128k "{output_video}" -y'
        
        await msg.edit(f"🎬 جاري حرق الترجمة وحذف القديم ({quality}p)...")
        subprocess.run(cmd, shell=True, check=True)

        # إرسال الفيديو النهائي
        await msg.edit("📤 جاري الرفع إلى تيليجرام...")
        await client.send_video(user_id, output_video, caption=f"✅ تم الإنجاز بجودة {quality}p\n🔥 تم تطهير الفيديو من الترجمات السابقة.")
        
    except Exception as e:
        await client.send_message(user_id, f"❌ فشلت العملية: {str(e)}")
    finally:
        # تنظيف الملفات المؤقتة
        if os.path.exists(output_video): os.remove(output_video)
        subprocess.run(f'rm -rf {download_dir}', shell=True)

app.run()
