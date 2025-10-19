import os
import io
import json
from datetime import datetime
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from notion_client import Client
import google.generativeai as genai

# ─────────────────────────────
#  ENVIRONMENT SETUP
# ─────────────────────────────
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DOCUMENT_DB_ID = os.getenv("NOTION_NOTES_DB_ID")

if not GOOGLE_API_KEY or not NOTION_TOKEN or not DOCUMENT_DB_ID:
    raise ValueError("Missing required API keys or Notion DB ID in .env file")

# Configure Gemini + Notion
genai.configure(api_key=GOOGLE_API_KEY)
notion = Client(auth=NOTION_TOKEN)

# ─────────────────────────────
#  GEMINI-BASED TEXT EXTRACTION
# ─────────────────────────────
def extract_text_and_title(file_path: str) -> tuple[str, str]:
    """
    Extract text or OCR content from any file using Gemini,
    and generate a suitable title from the content.
    Returns (title, text).
    """
    ext = os.path.splitext(file_path)[1].lower()
    fname = os.path.basename(file_path)
    print(f"[Gemini OCR] Processing: {fname}")

    model = genai.GenerativeModel("models/gemini-2.5-flash")

    # 1️⃣ Handle plain text files
    if ext in [".txt", ".md", ".csv"]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

    # 2️⃣ Handle image files
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]:
        prompt = (
            "Extract all visible text, labels, equations, and captions from this image "
            "as readable Markdown text. Then summarize it into a 3–7 word title."
        )

        with Image.open(file_path) as img:
            if hasattr(img, "n_frames") and img.n_frames > 1:
                img.seek(0)
            img = img.convert("RGB")
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            buffer.seek(0)

        response = model.generate_content(
            [prompt, {"mime_type": "image/jpeg", "data": buffer.read()}]
        )

        content = response.text.strip()

    # 3️⃣ Handle PDFs or unsupported formats
    else:
        with open(file_path, "rb") as f:
            content_bytes = f.read()
        prompt = (
            "Extract all text, tables, and key information from this document. "
            "Return as clean Markdown text and summarize into a concise 3–7 word title."
        )
        response = model.generate_content(
            [prompt, {"mime_type": "application/octet-stream", "data": content_bytes}]
        )
        content = response.text.strip()

    # 4️⃣ Generate a title from content (short, descriptive)
    title_prompt = (
        "Generate a short, descriptive title (max 7 words) for the following content:\n\n"
        f"{content[:2000]}"
    )
    title_response = model.generate_content(title_prompt)
    title = title_response.text.strip().replace('"', "")

    # Fallback if Gemini fails to name
    if not title or len(title) < 3:
        title = os.path.splitext(fname)[0]

    print(f"[Gemini OCR] ✅ Extracted title: {title}")
    return title, content


# ─────────────────────────────
#  NOTION UPLOAD FUNCTION
# ─────────────────────────────
def insert_document_to_notion(title: str, content: str, category: str = None) -> dict:
    """
    Create a new page in the Document Hub database.
    Fields:
      - Doc name (title)
      - Content (as rich_text paragraph)
      - Optional Category (multi_select)
    """
    if not DOCUMENT_DB_ID:
        raise ValueError("Missing DOCUMENT_DB_ID in .env")

    properties = {
        "Doc name": {"title": [{"text": {"content": title}}]},
    }

    if category:
        properties["Category"] = {"multi_select": [{"name": category}]}

    # Trim if too long for Notion block
    content_block = content[:1900] if len(content) > 1900 else content

    try:
        page = notion.pages.create(
            parent={"database_id": DOCUMENT_DB_ID},
            properties=properties,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content_block}}],
                    },
                }
            ],
        )
        print(f"✅ Uploaded '{title}' to Notion ({page.get('url')})")
        return page

    except Exception as e:
        print(f"❌ Notion insert failed: {e}")
        raise


# ─────────────────────────────
#  PIPELINE FUNCTION
# ─────────────────────────────
def process_and_upload_document(file_path: str, category: str = None):
    """
    Full pipeline: Extract text + auto-generate title + upload to Notion.
    """
    title, text = extract_text_and_title(file_path)
    return insert_document_to_notion(title, text, category)



def run_note_agent(file_path: str, category: str = None):
    """
    Controlled NoteAgent that only runs when explicitly called.
    Uses OCR Agent internally for text + title extraction, then uploads to Notion.
    Returns the Notion response (or raises on error).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    if not DOCUMENT_DB_ID:
        raise ValueError("Missing DOCUMENT_DB_ID in .env")

    print(f"📝 [NoteAgent] Processing file: {os.path.basename(file_path)}")
    title, content = extract_text_and_title(file_path)
    print(f"🧠 Extracted title: {title} ({len(content)} chars)")
    print("📤 Uploading to Notion Document Hub...")

    result = insert_document_to_notion(title, content, category)
    print(f"✅ Uploaded '{title}' to Notion ({result.get('url')})")

    return result

if __name__ == "__main__":
    file_path = "d:/Projects/tedai-gemini-desk/data/notes/cse130_note.jpg"
    process_and_upload_document(file_path, category="Planning")
