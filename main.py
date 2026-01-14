import yt_dlp
import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ExtractRequest(BaseModel):
    url: str

@app.post("/extract")
async def extract_video(data: ExtractRequest):
    url = data.url
    cookie_path = 'cookies.txt' 

    ydl_opts = {
        'format': 'best[height<=720][ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            
            if not video_url and 'formats' in info:
                for f in info['formats']:
                    if f.get('height') <= 720 and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        video_url = f.get('url')
                        break

            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "videoUrl": video_url,
                "thumbnail": info.get('thumbnail'), # Notification ke liye thumbnail
                "source": "youtube" if "youtu" in url else "instagram"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}