import os
import json
import httpx
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from notion_client import Client
from datetime import datetime, timedelta
import dateutil.parser

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
TASKS_DB_ID = os.getenv("NOTION_TASK_DB_ID", "")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

if not GEMINI_API_KEY or not NOTION_TOKEN or not TASKS_DB_ID:
    raise ValueError("Missing required API keys or database ID in .env file")

app = FastAPI()
notion = Client(auth=NOTION_TOKEN)

def normalize_status(value: str | None) -> str:
    """Map free text to valid Notion status options."""
    if not value:
        return "Not started"
    v = value.lower().strip()
    if any(k in v for k in ["progress", "doing", "ongoing"]):
        return "In progress"
    if any(k in v for k in ["done", "complete", "finished"]):
        return "Done"
    if any(k in v for k in ["not", "todo", "to do", "pending"]):
        return "Not started"
    # default
    return "Not started"


def normalize_date(value: str | None) -> str:
    """Convert natural date text to ISO 8601 (YYYY-MM-DD)."""
    if not value:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        # Try strict ISO parse
        return dateutil.parser.parse(value).date().isoformat()
    except Exception:
        # Gemini may give vague text like 'next week' or 'before spring break'
        text = value.lower()
        today = datetime.now()
        if "next week" in text:
            return (today + timedelta(days=7)).date().isoformat()
        if "spring" in text:
            return f"{today.year}-03-15"
        if "quarter" in text:
            return (today + timedelta(days=90)).date().isoformat()
        # Default: one week from now
        return (today + timedelta(days=7)).date().isoformat()
    
class ParseRequest(BaseModel):
    text: str

# Map natural language / Gemini fields → Notion schema names
PROPERTY_MAP = {
    "title": "Task name",
    "description": "Description",
    "due_date": "Due date",
    "priority": "Priority",
    "difficulty": "Effort level",
    "category": "Task type",
    "status": "Status",
    "assignee": "Assignee",
    "task_type": "Task type"
}

# Normalize to Notion allowed values
DEFAULTS = {
    "Priority": "Medium",
    "Effort level": "Medium",
    "Status": "Not started",
    # "Category": "General",
    "Task type": "💬 Feature request"
}


@app.post("/parse")
async def parse(req: ParseRequest):
    """Parse natural text into structured task and add to Notion"""
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "due_date": {"type": "string"},
            "priority": {"type": "string"},
            "difficulty": {"type": "string"},
            "category": {"type": "string"},
            "status": {"type": "string"},
            "assignee": {"type": "string"},
            "task_type": {"type": "string"}
        }
    }

    prompt = f"""
    You are a task parser. Given text, extract key details into this JSON schema:
    {json.dumps(schema, indent=2)}.
    Parse natural date/time into YYYY-MM-DD if possible.
    Use descriptive task titles and fill missing fields sensibly.
    TEXT:
    {req.text}
    """

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema
        }
    }

    # ── Step 1: Ask Gemini
    async with httpx.AsyncClient(timeout=40) as client:
        r = await client.post(GEMINI_URL, json=payload)
        if r.status_code != 200:
            raise HTTPException(500, detail=f"Gemini error: {r.text}")
        data = r.json()

    try:
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        task = json.loads(raw)
    except Exception as e:
        raise HTTPException(500, detail=f"Parse error: {e}\n{data}")

    # ── Step 2: Map parsed task to Notion properties
    notion_props = {}

    for key, value in task.items():
        if not value:
            continue  # skip empty fields
        notion_key = PROPERTY_MAP.get(key)
        if not notion_key:
            continue

        match notion_key:
            case "Task name":
                notion_props[notion_key] = {"title": [{"text": {"content": value}}]}
            case "Description":
                notion_props[notion_key] = {"rich_text": [{"text": {"content": value}}]}
            case "Due date":
                iso_date = normalize_date(value)
                notion_props[notion_key] = {"date": {"start": iso_date}}
            case "Priority" | "Effort level":
                notion_props[notion_key] = {"select": {"name": value}}
            case "Status":
                clean_status = normalize_status(value)
                notion_props[notion_key] = {"status": {"name": clean_status}}
            case "Category":
                notion_props[notion_key] = {"multi_select": [{"name": value}]}
            case "Task type":
                notion_props[notion_key] = {"multi_select": [{"name": value}]}
            case "Assignee":
                # You can extend this by resolving user IDs dynamically
                notion_props[notion_key] = {
                    "people": []  # placeholder, since Notion API needs user IDs
                }

    # Fill in defaults for any required fields missing
    for prop, default_value in DEFAULTS.items():
        if prop not in notion_props:
            if prop in ["Priority", "Effort level", "Status"]:
                notion_props[prop] = {"select": {"name": default_value}}
            elif prop in ["Category", "Task type"]:
                notion_props[prop] = {"multi_select": [{"name": default_value}]}

    # ── Step 3: Add to Notion
    try:
        created = notion.pages.create(
            parent={"database_id": TASKS_DB_ID},
            properties=notion_props
        )
    except Exception as e:
        raise HTTPException(500, detail=f"Notion insert failed: {e}")

    # ── Step 4: Return combined result
    return {
        "message": "✅ Task added to Notion successfully!",
        "parsed_task": task,
        "mapped_properties": notion_props,
        "notion_page_url": created.get("url")
    }
