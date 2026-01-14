import yt_dlp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ExtractRequest(BaseModel):
    url: str

@app.post("/extract")
async def extract_video(data: ExtractRequest):
    # Snaptube style: Sirf direct URLs aur metadata uthana
    ydl_opts = {
        'format': 'best[height<=720][ext=mp4]/best', # Sirf 720p mang rahe hain
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
        # Yeh headers zaroori hain YouTube ko dhokha dene ke liye
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data.url, download=False)
            
            # Direct link nikalna (YouTube itag 22 ya Instagram best link)
            video_url = info.get('url')
            if not video_url and 'formats' in info:
                # Combined format dhundna (vcodec aur acodec dono ho)
                for f in info['formats']:
                    if f.get('height') <= 720 and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        video_url = f.get('url')
                        break
            
            if not video_url:
                raise Exception("Direct link not found")

            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "videoUrl": video_url,
                "thumbnail": info.get('thumbnail'),
                "source": "youtube" if "youtu" in data.url else "instagram"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}