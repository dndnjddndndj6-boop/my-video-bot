import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import threading
from flask import Flask

# إنشاء سيرفر وهمي لإبقاء البوت حياً في Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is Running!"

def run_web_app():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# تشغيل السيرفر في خلفية البرنامج
threading.Thread(target=run_web_app, daemon=True).start()

# --- بقية كود البوت الخاص بك تبدأ من هنا ---
API_ID = 32370962
# ... كمل الكود للنهاية ...


API_ID = 32370962
API_HASH = "8d41f5c8b0f5e4efa0a74e13a02e41f7"
BOT_TOKEN = "8304901124:AAHsFSAyhd5jQs_5zkZGbg4ZO97rYSSniwk"

app = Client("subtitle_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

@app.on_message(filters.document)
async def handle_docs(client, message):
    if message.document.file_name.endswith(('.srt', '.ass')):
        user_data[message.from_user.id] = {'sub': await message.download()}
        await message.reply("✅ تم حفظ الترجمة. أرسل الآن رابط الفيديو.")

@app.on_message(filters.text & filters.regex(r'^http.*'))
async def handle_link(client, message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return await message.reply("❌ أرسل ملف الترجمة أولاً!")
    
    user_data[user_id]['url'] = message.text
    
    # أزرار اختيار الجودة
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("1080p (الجودة الأصلية)", callback_data="1080")],
        [InlineKeyboardButton("720p (توازن ممتاز)", callback_data="720")],
        [InlineKeyboardButton("480p (مساحة صغيرة)", callback_data="480")]
    ])
    await message.reply("اختر الجودة المطلوبة للبدء بالحرق والضغط:", reply_markup=buttons)

@app.on_callback_query()
async def process_video(client, callback_query):
    user_id = callback_query.from_user.id
    quality = callback_query.data
    url = user_data[user_id]['url']
    sub = user_data[user_id]['sub']
    output_file = f"video_{quality}p.mp4"
    
    await callback_query.message.edit(f"⏳ جاري المعالجة بجودة {quality}p... قد يستغرق الأمر دقائق.")
    
    # ضبط الإعدادات حسب اختيارك
    if quality == "1080":
        scale = "" # لا يوجد تغيير في الحجم
        crf = "23" # جودة عالية
    elif quality == "720":
        scale = "scale=1280:-2,"
        crf = "26"
    else: # 480p
        scale = "scale=854:-2,"
        crf = "28"

    cmd = f'ffmpeg -i "{url}" -vf "{scale}subtitles={sub}" -c:v libx264 -crf {crf} -preset faster -c:a aac -b:a 128k "{output_file}" -y'
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        await client.send_video(user_id, output_file, caption=f"✅ تم الانتهاء بجودة {quality}p")
    except Exception as e:
        await client.send_message(user_id, f"❌ حدث خطأ: {str(e)}")
    finally:
        if os.path.exists(output_file): os.remove(output_file)

app.run()
