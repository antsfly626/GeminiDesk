from fastapi import FastAPI
from pydantic import BaseModel
from notion_client import Client
import os
from dotenv import load_dotenv
from notion_client.errors import APIResponseError
import json
import traceback

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
notion = Client(auth=NOTION_TOKEN)

app = FastAPI(title="Notion MCP Server")

class Query(BaseModel):
    database_id: str = None
    query: dict = None
    page_id: str = None
    title: str = None
    content: str = None

@app.get("/")
def root():
    return {"message": "✅ Notion MCP Server running"}

# --- Database tools ---

@app.post("/query_database")
def query_database(q: Query):
    try:
        if not q.database_id:
            return {"error": "Missing database_id"}

        response = notion.databases.query(
            database_id=q.database_id,
            **(q.query or {})
        )
        return response

    except APIResponseError as e:
        # Handle Notion API errors safely across versions
        raw_body = getattr(e, "body", None)
        try:
            # Convert string body to dict if needed
            error_info = json.loads(raw_body) if isinstance(raw_body, str) else (raw_body or {})
        except Exception:
            error_info = {}

        # Defensive: .response may not exist in some versions
        status_code = getattr(e, "status", None)
        if not status_code and hasattr(e, "response"):
            status_code = getattr(e.response, "status_code", None)

        return {
            "error": error_info.get("message", str(e)),
            "code": error_info.get("code", None),
            "status": status_code,
        }

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
    
@app.post("/create_page")
def create_page(q: Query):
    new_page = notion.pages.create(
        parent={"database_id": q.database_id},
        properties={
            "Name": {"title": [{"text": {"content": q.title}}]},
        },
    )
    return new_page

@app.get("/get_page/{page_id}")
def get_page(page_id: str):
    return notion.pages.retrieve(page_id)

# --- Search endpoint ---
@app.get("/search")
def search(q: str):
    return notion.search(query=q)
