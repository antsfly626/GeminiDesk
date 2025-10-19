import json
import os
from datetime import datetime, timedelta
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from google import genai
from google.genai.types import GenerateContentConfig, Schema, Type
from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

load_dotenv()

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
    participants: List[str] = []
    notes: str
    created_at: str
    # NEW: include these so FastAPI doesn't drop them
    calendar_url: Optional[str] = None
    error: Optional[str] = None

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

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service(port: int = 8080):
    """Authenticate and return a Google Calendar service client."""
    creds = None
    token_path = "token.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        # Force re-auth if scopes in token don't match desired SCOPES
        if not getattr(creds, "scopes", None) or set(creds.scopes) != set(SCOPES):
            creds = None  # discard and re-auth

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            # bind OAuth local server to the given port (avoid conflicts in tests)
            creds = flow.run_local_server(port=port)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)

def create_calendar_event(event_data: dict, port: int = 8080):
    """Create an event on Google Calendar using parsed Gemini data."""
    service = get_calendar_service(port=port)

    start = event_data.get("start_time")
    end = event_data.get("end_time")

    # Default fallback → 1-hour event starting now
    if not start:
        now = datetime.now()
        start = now.isoformat()
        end = (now + timedelta(hours=1)).isoformat()
    elif not end and event_data.get("duration_minutes"):
        try:
            dur = int(event_data["duration_minutes"])
        except Exception:
            dur = 60
        end = (datetime.fromisoformat(start) + timedelta(minutes=dur)).isoformat()
    elif not end:
        end = (datetime.fromisoformat(start) + timedelta(hours=1)).isoformat()

    body = {
        "summary": event_data.get("title", "Untitled Event"),
        "description": event_data.get("notes", ""),
        "start": {"dateTime": start, "timeZone": "America/Los_Angeles"},
        "end": {"dateTime": end, "timeZone": "America/Los_Angeles"},
    }

    # Optional fields — add only if valid
    if event_data.get("location"):
        body["location"] = event_data["location"]

    recurrence = event_data.get("recurrence")
    if recurrence and isinstance(recurrence, str) and recurrence.upper().startswith("RRULE:"):
        body["recurrence"] = [recurrence]
    else:
        # ensure default: not recurring
        body["recurrence"] = None

    created = service.events().insert(calendarId="primary", body=body).execute()
    return created.get("htmlLink")

def parse_with_gemini(text: str) -> Dict[str, Any]:
    """Use Gemini reasoning to extract event info."""
    prompt = f"""
    You are an intelligent calendar assistant.
    Analyze the following text and extract structured event data.

    Input: "{text}"

    Return a JSON object with fields:
    title, start_time, end_time, duration_minutes, recurrence, location,
    participants, notes, created_at.

    If uncertain about any field, leave it null.
    """

    config = GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=calendar_schema,
    )

    response = client.models.generate_content(
        model="models/gemini-2.5-flash-lite",
        contents=prompt,
        config=config
    )

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
    try:
        # use default port=8080 for server mode; tests can pass 8082 directly
        calendar_link = create_calendar_event(event, port=8080)
        event["calendar_url"] = calendar_link
    except Exception as e:
        event["calendar_url"] = None
        event["error"] = str(e)
    return event

if __name__ == "__main__":
    import uvicorn
    # IMPORTANT: module path must match this file's package path
    uvicorn.run("app.agents.cal_agent:app", host="0.0.0.0", port=8002, reload=True)
