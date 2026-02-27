import os
import yt_dlp

def download_video(url, output_dir='downloads', quality='best', cookies_file=None):
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': quality,  # 'best' বা '720p' বা 'bestaudio' (MP3-এর জন্য)
        'noplaylist': True,
        'quiet': False,  # প্রোগ্রেস দেখাবে
    }
    
    # অ্যাডাল্ট সাইটের জন্য কুকিজ যোগ করা (যদি দরকার হয়)
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file  # কুকিজ ফাইল (Netscape ফরম্যাট)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ ডাউনলোড সম্পন্ন!")
    except Exception as e:
        print(f"❌ সমস্যা: {str(e)}")

# উদাহরণ ব্যবহার
if __name__ == "__main__":
    video_url = input("ভিডিও লিঙ্ক দাও (যেমন Pornhub বা Xvideos): ")
    cookies_path = input("কুকিজ ফাইলের পথ দাও (যদি না থাকে Enter চাপো): ") or None
    download_video(video_url, quality='best', cookies_file=cookies_path)
