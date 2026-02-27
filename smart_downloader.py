import os
import asyncio
import uuid
from pathlib import Path
from dotenv import load_dotenv

import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise ValueError("❌ .env ফাইলে API_ID / API_HASH / BOT_TOKEN পাওয়া যায়নি!")

API_ID = int(API_ID)

app = Client("smart_dl_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOADS = Path("downloads")
DOWNLOADS.mkdir(exist_ok=True)


def main_menu(url=None):
    if url:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎥 ভিডিও (720p • ছোট)", callback_data=f"vid_{url}"),
                InlineKeyboardButton("🎧 MP3 (হাই কোয়ালিটি)", callback_data=f"aud_{url}"),
            ],
            [InlineKeyboardButton("✨ নতুন লিঙ্ক", callback_data="new_link")]
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("লিঙ্ক পাঠাও ✨", callback_data="new_link")]
    ])


async def progress(current, total, msg):
    try:
        percent = round(current * 100 / total, 1)
        await msg.edit_text(f"📤 আপলোড হচ্ছে... {percent}%")
    except:
        pass


@app.on_message(filters.private & filters.command("start"))
async def start(_, msg):
    await msg.reply(
        "🌟 **হ্যালো! স্বাগতম আমার ডাউনলোডার বটে** 🌟\n\n"
        "ইউটিউব • ফেসবুক • টিকটক • ইনস্টা — যেকোনো লিঙ্ক পাঠাও\n"
        "আমি ভিডিও বা MP3 দিয়ে দেব ❤️",
        reply_markup=main_menu()
    )


@app.on_message(filters.private & filters.regex(r"https?://"))
async def link_handler(_, msg):
    url = msg.text.strip()
    await msg.reply(
        "✅ **লিঙ্ক পেয়েছি!**\nকোনটা চাও?",
        reply_markup=main_menu(url)
    )


@app.on_callback_query(filters.regex(r"^(vid|aud)_"))
async def download(client, cb: CallbackQuery):
    mode, url = cb.data.split("_", 1)
    status = await cb.message.edit_text("⏳ প্রসেসিং চলছে... একটু অপেক্ষা করো")

    uid = uuid.uuid4().hex[:10]
    outtmpl = str(DOWNLOADS / f"{uid}_%(title)s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
    }

    if mode == "vid":
        ydl_opts["format"] = "bestvideo[height<=?720][ext=mp4]+bestaudio/best[height<=?720]"
    else:
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        })

    file_path = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            file_path = ydl.prepare_filename(info)
            if mode == "aud" and not file_path.lower().endswith(".mp3"):
                file_path = file_path.rsplit(".", 1)[0] + ".mp3"

        await status.edit_text("🚀 টেলিগ্রামে পাঠাচ্ছি...")
        send_kw = {"chat_id": cb.message.chat.id, "progress": progress, "progress_args": (status,)}

        if mode == "vid":
            await client.send_video(file_path, caption="🎥 ভিডিও রেডি! (720p)", **send_kw)
        else:
            await client.send_audio(file_path, caption="🎧 MP3 • 192kbps", **send_kw)

        await status.edit_text(
            "🎉 **সম্পন্ন!** আরও কিছু চাও?",
            reply_markup=main_menu(url)
        )

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await status.edit_text("🚦 টেলিগ্রাম লিমিট → একটু পর আবার চেষ্টা করো")
    except Exception as e:
        await status.edit_text(f"😔 সমস্যা: {str(e)[:150]}", reply_markup=main_menu(url))
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@app.on_callback_query(filters.regex("^new_link$"))
async def new_link_cb(_, cb: CallbackQuery):
    await cb.message.edit_text("নতুন লিঙ্ক পাঠাও... 🌟")
    await cb.answer()


if __name__ == "__main__":
    print("🌟 বট চালু হচ্ছে... 🌟")
    app.run()
