import os, json, httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


app = FastAPI()


class ParseRequest(BaseModel):
    text: str


@app.post("/parse")
async def parse(req: ParseRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(500, detail="Missing GEMINI_API_KEY")


    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "due_date": {"type": "string"},
            "time_start": {"type": "string"},
            "time_estimate": {"type": "string"},
            "difficulty": {"type": "string"},
            "category": {"type": "string"},
            "location": {"type": "string"},
            "recurring": {
                "type": "object",
                "properties": {
                    "frequency": {"type": "string", "description": "daily, weekly, monthly, etc."},
                    "interval": {"type": "integer", "description": "how often, e.g. every 2 weeks"},
                    "end_date": {"type": "string", "description": "optional end date"}
                }
            }
        }
    }


    prompt = f"Extract key task details as JSON per this schema.\nTEXT:\n{req.text}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "responseSchema": schema}
    }


    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(GEMINI_URL, json=payload)
        if r.status_code != 200:
            raise HTTPException(500, detail=f"Gemini error: {r.text}")
        data = r.json()


    try:
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw)
    except Exception as e:
        raise HTTPException(500, detail=f"Parse error: {e}\n{data}")