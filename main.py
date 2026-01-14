import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ExtractRequest(BaseModel):
    url: str

@app.get("/rules")
async def get_rules():
    # Yeh JS rules hain jo App ke WebView mein run honge
    return {
        "instagram": "document.querySelector('meta[property=\"og:video\"]')?.content || document.querySelector('video')?.src",
        "youtube": "window.ytInitialPlayerResponse.streamingData.formats.filter(f => f.itag === 22 || f.height <= 720)[0].url",
        "linkedin": "document.querySelector('video')?.src"
    }

@app.post("/info")
async def get_info(data: ExtractRequest):
    url = data.url.strip().split('?')[0]
    if "instagram.com/reels/" in url:
        url = url.replace("/reels/", "/p/")
    
    # Hum heavy yt-dlp nahi chalayenge, sirf basic info filter karenge
    return {
        "clean_url": url,
        "is_youtube": "youtube.com" in url or "youtu.be" in url,
        "is_instagram": "instagram.com" in url
    }