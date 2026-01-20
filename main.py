import os, threading, subprocess
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 1. إعداد السيرفر الوهمي أولاً لإرضاء Render
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Running!"
def run_web_app():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_web_app, daemon=True).start()

# 2. تعريف متغير البوت (هذا هو السطر الذي كان يسبب الخطأ)
API_ID = 32370962
API_HASH = "8d41f5c8b0f5e4efa0a74e13a02e41f7"
BOT_TOKEN = "8304901124:AAHsFSAyhd5jQs_5zkZGbg4ZO97rYSSniwk"

app = Client("subtitle_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}

# 3. الأوامر والوظائف (يجب أن تأتي بعد تعريف app)
@app.on_message(filters.document)
async def handle_docs(client, message):
    if message.document.file_name.endswith(('.srt', '.ass')):
        user_data[message.from_user.id] = {'sub': await message.download()}
        await message.reply("✅ تم حفظ الترجمة. أرسل الآن رابط Magnet.")

@app.on_message(filters.text & (filters.regex(r'^http.*') | filters.regex(r'^magnet:.*')))
async def handle_link(client, message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return await message.reply("❌ أرسل ملف الترجمة أولاً!")
    user_data[user_id]['url'] = message.text
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("1080p", callback_data="1080")],
        [InlineKeyboardButton("720p", callback_data="720")],
        [InlineKeyboardButton("480p", callback_data="480")]
    ])
    await message.reply("اختر الجودة المطلوبة (سيتم حذف أي ترجمة سابقة وحرق ترجمتك):", reply_markup=buttons)

@app.on_callback_query()
async def process_video(client, callback_query):
    user_id = callback_query.from_user.id
    quality = callback_query.data
    url = user_data[user_id]['url']
    sub = user_data[user_id]['sub']
    await callback_query.message.edit(f"⏳ جاري التحميل والمعالجة جودة {quality}p... قد يستغرق وقتًا.")
    
    downloaded_file = "input_video"
    output_file = f"final_{quality}p.mp4"

    # تحميل Magnet
    if url.startswith("magnet:"):
        subprocess.run(f'aria2c --follow-magnet=mem --seed-time=0 "{url}" -d . -o {downloaded_file}', shell=True)
    else:
        subprocess.run(f'wget "{url}" -O {downloaded_file}', shell=True)

    scale = ""
    if quality == "720": scale = "scale=1280:-2,"
    elif quality == "480": scale = "scale=854:-2,"

    # -sn لحذف الترجمات القديمة و -vf لحرق الجديدة
    cmd = f'ffmpeg -i "{downloaded_file}" -vf "{scale}subtitles={sub}" -sn -c:v libx264 -crf 26 -preset faster -c:a aac -b:a 128k "{output_file}" -y'
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        await client.send_video(user_id, output_file, caption=f"✅ تم الانتهاء بجودة {quality}p")
    except Exception as e:
        await client.send_message(user_id, f"❌ حدث خطأ: {str(e)}")
    finally:
        for f in [downloaded_file, output_file]:
            if os.path.exists(f): os.remove(f)

app.run()
