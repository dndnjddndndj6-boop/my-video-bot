# ... (جزء Flask و السيرفر الوهمي يبقى كما هو في البداية) ...

@app.on_callback_query()
async def process_video(client, callback_query):
    user_id = callback_query.from_user.id
    quality = callback_query.data
    url = user_data[user_id]['url']
    sub = user_data[user_id]['sub']
    
    await callback_query.message.edit(f"📥 جاري تحميل التورنت ومعالجة جودة {quality}p... انتظر قليلاً.")
    
    downloaded_file = "input_video.mkv"
    output_file = f"final_{quality}p.mp4"

    # 1. أمر تحميل الـ Magnet باستخدام aria2
    if url.startswith("magnet:"):
        subprocess.run(f'aria2c --follow-magnet=mem --seed-time=0 "{url}" -d . -o {downloaded_file}', shell=True)
    else:
        subprocess.run(f'wget "{url}" -O {downloaded_file}', shell=True)

    # 2. إعدادات الجودة وحذف الترجمات القديمة (-sn)
    scale = ""
    if quality == "720": scale = "scale=1280:-2,"
    elif quality == "480": scale = "scale=854:-2,"

    # الأمر السحري: -sn يحذف الترجمات القديمة، و -vf يحرق ترجمتك الجديدة
    cmd = f'ffmpeg -i "{downloaded_file}" -vf "{scale}subtitles={sub}" -sn -c:v libx264 -crf 26 -preset faster -c:a aac -b:a 128k "{output_file}" -y'
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        await client.send_video(user_id, output_file, caption=f"✅ تم حذف الترجمات القديمة وحرق ترجمتك بنجاح ({quality}p)")
    except Exception as e:
        await client.send_message(user_id, f"❌ خطأ: {str(e)}")
    finally:
        for f in [downloaded_file, output_file]:
            if os.path.exists(f): os.remove(f)
