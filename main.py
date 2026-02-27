import os
import asyncio
import uuid
from pathlib import Path

import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait

# ────────────────────────────────────────────────
API_ID   = 1234567               # আপনার API ID
API_HASH = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
BOT_TOKEN = "8629417255:AAERgnBzVr25QhMXD-9_vr2cri_7uXu6pfc"
# ────────────────────────────────────────────────

app = Client("smart_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


def get_main_menu(url: str = None) -> InlineKeyboardMarkup:
    """মূল মেনু বোতাম তৈরি করে"""
    if url:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎬 ভিডিও (720p, ছোট সাইজ)", callback_data=f"vid_{url}"),
                InlineKeyboardButton("🎵 MP3 (হাই কোয়ালিটি)", callback_data=f"aud_{url}"),
            ],
            [
                InlineKeyboardButton("🔄 অন্য লিঙ্ক দাও", callback_data="new_link"),
            ]
        ])
    else:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("নতুন লিঙ্ক দিন →", url="https://t.me/yourbot?start=new"),
            ]
        ])


async def progress(current, total, message):
    percent = current * 100 / total
    try:
        await message.edit_text(f"📤 আপলোড হচ্ছে... {percent:.1f}%")
    except:
        pass  # edit fail হলে ignore


@app.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    text = (
        "👋 **স্বাগতম স্মার্ট ডাউনলোডার বটে!**\n\n"
        "শুধু ইউটিউব / ফেসবুক / টিকটক / ইনস্টাগ্রাম যেকোনো লিঙ্ক পাঠান।\n"
        "আমি ভিডিও অথবা MP3 দিয়ে দেব ✓"
    )
    await message.reply_text(text)


@app.on_message(filters.private & filters.regex(r'(https?://[^\s]+)'))
async def link_handler(client, message):
    url = message.matches[0].group(0).strip()

    await message.reply_text(
        "✅ **লিঙ্ক পেয়েছি!**\nকোন ফরম্যাটে ডাউনলোড করতে চান?",
        reply_markup=get_main_menu(url)
    )


@app.on_callback_query(filters.regex(r"^(vid|aud)_"))
async def download_callback(client, callback: CallbackQuery):
    mode, url = callback.data.split("_", 1)
    status = await callback.message.edit_text("⏳ yt-dlp দিয়ে প্রসেসিং চলছে...")

    unique = uuid.uuid4().hex[:10]
    outtmpl = str(DOWNLOAD_DIR / f"{unique}_%(title)s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    if mode == "vid":
        ydl_opts["format"] = "bestvideo[height<=?720][ext=mp4]+bestaudio[ext=m4a]/best[height<=?720]"
    else:
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })

    file_path = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            file_path = ydl.prepare_filename(info)

            if mode == "aud" and not file_path.lower().endswith(".mp3"):
                file_path = file_path.rsplit(".", 1)[0] + ".mp3"

        await status.edit_text("📤 টেলিগ্রামে পাঠাচ্ছি... (একটু সময় লাগতে পারে)")

        send_kw = {
            "chat_id": callback.message.chat.id,
            "progress": progress,
            "progress_args": (status,),
        }

        if mode == "vid":
            await client.send_video(video=file_path, caption="🎬 ভিডিও (720p পর্যন্ত)", **send_kw)
        else:
            await client.send_audio(audio=file_path, caption="🎵 MP3 • 192kbps", **send_kw)

        await status.edit_text(
            "✅ **ডাউনলোড সম্পন্ন!**\nআরেকটা লিঙ্ক দিতে চান?",
            reply_markup=get_main_menu(url)   # আবার মেনু দেখাচ্ছে
        )

    except yt_dlp.utils.DownloadError as e:
        await status.edit_text(f"❌ ডাউনলোড ফেল হয়েছে\n{str(e)[:180]}", reply_markup=get_main_menu(url))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await status.edit_text("⏱️ টেলিগ্রাম লিমিট → ৩০ সেকেন্ড পর আবার চেষ্টা করুন")
    except Exception as e:
        await status.edit_text(
            f"⚠️ সমস্যা হয়েছে\n{type(e).__name__}: {str(e)[:140]}",
            reply_markup=get_main_menu(url)
        )
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@app.on_callback_query(filters.regex("^new_link$"))
async def new_link(client, callback: CallbackQuery):
    await callback.message.edit_text(
        "নতুন লিঙ্ক পাঠান...\n(ইউটিউব / ফেসবুক / টিকটক / ইনস্টা যেকোনো লিঙ্ক)"
    )
    await callback.answer()


if __name__ == "__main__":
    print("Smart Downloader Bot চালু হচ্ছে...")
    app.run()
