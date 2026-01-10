import os
import re
from time import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

# Constants
MIN_DELAY = 7  # Increased slightly to be safer
LAST_REQUEST_TIME = 0

# Path check for Render environment vs Local environment
COOKIE_PATH = "/etc/secrets/cookies.txt" if os.path.exists("/etc/secrets/cookies.txt") else "cookies.txt"

class ExtractRequest(BaseModel):
    url: str
    quality: int = 1080

def clean_url(url: str):
    url = url.strip()
    # Convert Instagram Reels to Posts format (often more stable for extraction)
    if "instagram.com/reels/" in url:
        url = url.replace("/reels/", "/p/")
    # Remove query parameters from URL to clean it up
    url = url.split('?')[0]
    return url

@app.post("/extract")
async def extract_video(data: ExtractRequest):
    global LAST_REQUEST_TIME
    url = clean_url(data.url)
    preferred_height = data.quality or 1080

    is_instagram = "instagram.com" in url
    is_youtube = "youtube.com" in url or "youtu.be" in url

    if not (is_instagram or is_youtube):
        raise HTTPException(status_code=400, detail="Only Instagram and YouTube links are supported")

    # Rate Limit Logic
    if is_instagram:
        now = time()
        if now - LAST_REQUEST_TIME < MIN_DELAY:
            return JSONResponse(status_code=429, content={"error": "Rate limit: Please wait a few seconds."})
        LAST_REQUEST_TIME = now

    # Optimized yt-dlp Options
    ydl_opts = {
        "quiet": True,
        "no_warnings": False,
        "skip_download": True,
        "noplaylist": True,
        # Force it to find a direct mp4 link with audio
        "format": f"best[ext=mp4][height<={preferred_height}][vcodec!=none][acodec!=none]/best[ext=mp4]/best",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    if is_instagram:
        # Crucial: Instagram needs a referer header to look legitimate
        ydl_opts["referer"] = "https://www.instagram.com/"
        if os.path.exists(COOKIE_PATH):
            ydl_opts["cookiefile"] = COOKIE_PATH
        else:
            print(f"DEBUG: Cookie file not found at {COOKIE_PATH}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # We use download=False to just get the metadata
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise Exception("Failed to fetch video information")

            # Handle cases where the result is inside an 'entries' list (like Reels/Playlists)
            if "entries" in info:
                info = info["entries"][0]

            # Get the best available direct URL from formats if top-level url is missing
            video_url = info.get("url")
            if not video_url and "formats" in info:
                # Filter for mp4 formats with audio and video
                valid_formats = [f for f in info['formats'] if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                if valid_formats:
                    video_url = valid_formats[-1].get("url")

            return {
                "title": info.get("title", "Video"),
                "thumbnail": info.get("thumbnail"),
                "videoUrl": video_url,
                "quality": info.get("height"),
                "source": "instagram" if is_instagram else "youtube",
                "duration": info.get("duration"),
            }

    except Exception as e:
        error_msg = str(e)
        # Simplify error messages for the frontend
        if "login required" in error_msg.lower() or "401" in error_msg:
            error_msg = "Instagram login/cookies required."
        elif "429" in error_msg:
            error_msg = "Instagram rate limit reached. Try again later."
            
        return JSONResponse(status_code=400, content={"error": error_msg})