import json
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from google import genai
from google.genai.types import GenerateContentConfig, Schema, Type


# Make sure GOOGLE_API_KEY is set in your .env or environment
client = genai.Client()

app = FastAPI(title="GeminiDesk CalendarAgent (AI)", version="1.0")


class CalendarRequest(BaseModel):
    text: str


class CalendarEvent(BaseModel):
    title: str
    start_time: Optional[str]
    end_time: Optional[str]
    duration_minutes: Optional[int]
    recurrence: Optional[str]
    location: Optional[str]
    participants: List[str]
    notes: str
    created_at: str

calendar_schema = Schema(
    type=Type.OBJECT,
    properties={
        "title": Schema(type=Type.STRING, description="Short name of the event"),
        "start_time": Schema(type=Type.STRING, description="ISO8601 formatted start time"),
        "end_time": Schema(type=Type.STRING, description="ISO8601 formatted end time"),
        "duration_minutes": Schema(type=Type.INTEGER, description="Duration in minutes"),
        "recurrence": Schema(type=Type.STRING, description="Recurrence pattern, if any"),
        "location": Schema(type=Type.STRING, description="Event location, if mentioned"),
        "participants": Schema(type=Type.ARRAY, items=Schema(type=Type.STRING)),
        "notes": Schema(type=Type.STRING, description="Original input text or notes"),
        "created_at": Schema(type=Type.STRING, description="Time when this was generated (ISO format)")
    },
    required=["title", "notes", "created_at"]
)


def parse_with_gemini(text: str) -> Dict[str, Any]:
    """Use Gemini reasoning to extract event info."""

    prompt = f"""
    You are an intelligent calendar assistant. 
    Analyze the following text and extract structured event data.

    Input: "{text}"

    Return a JSON object with fields:
    title, start_time, end_time, duration_minutes, recurrence, location, participants, notes, created_at.

    If uncertain about any field, leave it null.
    """

    config = GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=calendar_schema,
    )

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=config
    )

    # Add fallback timestamp if missing
    data = json.loads(response.text)
    data.setdefault("created_at", datetime.now().isoformat())
    data.setdefault("notes", text)

    return data


@app.get("/")
def root():
    return {"message": "GeminiDesk CalendarAgent (AI) is running!"}


@app.post("/parse_event", response_model=CalendarEvent)
async def parse_event(req: CalendarRequest):
    event = parse_with_gemini(req.text)
    return event


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("calendar_agent:app", host="0.0.0.0", port=8002, reload=True)