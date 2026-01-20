import os, threading, subprocess, time
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Online"
def run_web_app():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_web_app, daemon=True).start()

API_ID = 32370962
API_HASH = "8d41f5c8b0f5e4efa0a74e13a02e41f7"
BOT_TOKEN = "8304901124:AAHsFSAyhd5jQs_5zkZGbg4ZO97rYSSniwk"

app = Client("subtitle_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}

@app.on_message(filters.document)
async def handle_docs(client, message):
    if message.document.file_name.endswith(('.srt', '.ass')):
        path = await message.download()
        user_data[message.from_user.id] = {'sub': path}
        await message.reply("✅ تم حفظ الترجمة. أرسل الآن رابط Magnet.")

@app.on_message(filters.text & (filters.regex(r'^http.*') | filters.regex(r'^magnet:.*')))
async def handle_link(client, message):
    if message.from_user.id not in user_data:
        return await message.reply("❌ أرسل ملف الترجمة أولاً!")
    user_data[message.from_user.id]['url'] = message.text
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("720p (توفير مساحة)", callback_data="720"),
         InlineKeyboardButton("480p (الأكثر أماناً)", callback_data="480")]
    ])
    await message.reply("⚠️ اختر جودة منخفضة لضمان عدم نفاد مساحة السيرفر:", reply_markup=buttons)

@app.on_callback_query()
async def process(client, callback_query):
    user_id = callback_query.from_user.id
    quality = callback_query.data
    url = user_data[user_id]['url']
    sub = user_data[user_id]['sub']
    
    msg = await callback_query.message.edit(f"📥 جاري التحميل بنظام توفير المساحة ({quality}p)...")
    work_dir = f"w_{user_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        # تحميل Magnet مع تقييد الذاكرة والقرص
        if "magnet:" in url:
            # إضافة --bt-max-peers=5 لتقليل استهلاك الرام والمساحة أثناء التحميل
            cmd_dl = f'aria2c --follow-magnet=mem --seed-time=0 --disk-cache=0 --direct-file-mapping=false --bt-max-peers=5 "{url}" -d {work_dir}'
            subprocess.run(cmd_dl, shell=True, check=True)
        else:
            subprocess.run(f'wget "{url}" -P {work_dir}', shell=True, check=True)

        video_file = None
        for root, _, files in os.walk(work_dir):
            if files:
                video_file = max([os.path.join(root, f) for f in files], key=os.path.getsize)
        
        if not video_file: raise Exception("لم يتم الع found الفيديو")

        output = f"out_{user_id}.mp4"
        # زيادة CRF لتقليل حجم الفيديو الناتج وحجم الملفات المؤقتة
        scale = "scale=1280:-2," if quality == "720" else "scale=854:-2,"
        cmd_ff = f'ffmpeg -i "{video_file}" -vf "{scale}subtitles={sub}" -sn -c:v libx264 -crf 30 -preset ultrafast -c:a aac -b:a 96k "{output}" -y'
        
        await msg.edit("🎬 جاري المعالجة (Ultrafast Mode)...")
        subprocess.run(cmd_ff, shell=True, check=True)
        
        await msg.edit("📤 جاري الرفع...")
        await client.send_video(user_id, output, caption=f"✅ تم الإنجاز ({quality}p)")
        
    except Exception as e:
        await client.send_message(user_id, f"❌ حدث خطأ (غالباً بسبب المساحة): {str(e)}")
    finally:
        # مسح فوري لكل شيء لتفريغ المساحة للمرة القادمة
        if os.path.exists(output): os.remove(output)
        subprocess.run(f"rm -rf {work_dir}", shell=True)

app.run()
