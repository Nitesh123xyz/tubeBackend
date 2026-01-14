from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ExtractRequest(BaseModel):
    url: str

@app.post("/info")
async def get_info(data: ExtractRequest):
    url = data.url.strip().split('?')[0]
    # Instagram reels ko post format mein badalna extraction ke liye behtar hai
    if "instagram.com/reels/" in url:
        url = url.replace("/reels/", "/p/")
    
    return {
        "clean_url": url,
        "is_youtube": "youtube.com" in url or "youtu.be" in url,
        "is_instagram": "instagram.com" in url
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)