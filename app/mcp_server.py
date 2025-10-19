from fastapi import FastAPI
from pydantic import BaseModel
from notion_client import Client
import os
from dotenv import load_dotenv

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
    result = notion.databases.query(database_id=q.database_id, **(q.query or {}))
    return result

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
