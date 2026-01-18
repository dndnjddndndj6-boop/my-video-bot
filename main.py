import os
import subprocess
import time
import libtorrent as lt
from pyrogram import Client, filters

# --- بياناتك الشخصية ---
API_ID = 32370962
API_HASH = "8d41f5c8b0f5e4efa0a74e13a02e41f7"
BOT_TOKEN = "8304901124:AAHsFSAyhd5jQs_5zkZGbg4ZO97rYSSniwk"

app = Client("subtitle_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_subs = {}

@app.on_message(filters.document)
async def handle_docs(client, message):
    file_name = message.document.file_name
    if file_name.endswith(('.srt', '.ass')):
        path = await message.download()
        user_subs[message.from_user.id] = path
        await message.reply("✅ استلمت ملف الترجمة. الآن أرسل رابط الماجنت (Magnet Link).")

@app.on_message(filters.text & filters.regex(r'^magnet:.*'))
async def handle_magnet(client, message):
    user_id = message.from_user.id
    if user_id not in user_subs:
        await message.reply("❌ أرسل ملف الترجمة (.srt أو .ass) أولاً!")
        return

    magnet_link = message.text
    status_msg = await message.reply("⏳ بدأت عملية تحميل التورنت... قد يستغرق ذلك وقتاً.")

    ses = lt.session()
    params = {
        'save_path': '.',
        'storage_mode': lt.storage_mode_t.storage_mode_sparse,
    }
    handle = lt.add_magnet_uri(ses, magnet_link, params)
    
    while not handle.has_metadata():
        time.sleep(1)
    
    await status_msg.edit("✅ تم جلب بيانات التورنت، جاري التحميل الآن...")
    
    while handle.status().state != lt.torrent_status.seeding:
        time.sleep(5)
    
    file_name = handle.get_torrent_info().name()
    output = "final_video.mp4"
    
    await status_msg.edit("🎬 جاري دمج الترجمة مع الفيديو... انتظر قليلاً.")

    # أمر FFmpeg المعدل: دمج الترجمة فقط بدون شعار
    cmd = f'ffmpeg -i "{file_name}" -vf "subtitles=\'{user_subs[user_id]}\'" -c:v libx264 -crf 23 -c:a aac "{output}" -y'

    subprocess.run(cmd, shell=True)

    await status_msg.edit("🚀 جاري رفع الفيديو النهائي لتيليجرام...")
    await message.reply_video(output, caption="✅ تم الدمج بنجاح (بدون شعار)!")
    
    # تنظيف الملفات لزيادة المساحة
    if os.path.exists(output): os.remove(output)
    if os.path.exists(file_name): os.remove(file_name)
    if user_id in user_subs:
        if os.path.exists(user_subs[user_id]): os.remove(user_subs[user_id])
        del user_subs[user_id]

print("البوت يعمل الآن بدون شعار...")
app.run()
