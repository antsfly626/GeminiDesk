# app/agents/router_agent.py
import os
import json
import google.generativeai as genai
from app.agents.ocr_agent import extract_text  # ✅ directly reuse OCR
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


BASE_DIR = Path(__file__).resolve().parent  # folder of current file
DATA_DIR = BASE_DIR.parent.parent /"data"


SYSTEM_PROMPT = """
You are a document classifier. Analyze the following text and decide the best agent:
- NoteAgent: organizes notes
- FinanceAgent: extracts receipts and budgets
- TaskAgent: schedules tasks
- EventAgent: adds events to calendar

Return JSON only in this format:
{"agent": "<AgentName>", "confidence": <float>, "content": "<short description>"}
"""

def route_text(text: str) -> dict:
    """Send text to Gemini and return structured JSON classification."""
    model = genai.GenerativeModel(
        "models/gemini-2.5-flash",
        generation_config={
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
    )
import google.generativeai as genai
from app.agents.ocr_agent import extract_text  # ✅ directly reuse OCR
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


BASE_DIR = Path(__file__).resolve().parent  # folder of current file
DATA_DIR = BASE_DIR.parent.parent /"data"


SYSTEM_PROMPT = """
You are a document classifier. Analyze the following text and decide the best agent:
- NoteAgent: organizes notes
- FinanceAgent: extracts receipts and budgets
- TaskAgent: schedules tasks
- EventAgent: adds events to calendar

Return JSON only in this format:
{"agent": "<AgentName>", "confidence": <float>, "content": "<short description>"}
"""

def route_text(text: str) -> dict:
    """Send text to Gemini and return structured JSON classification."""
    model = genai.GenerativeModel(
        "models/gemini-2.5-flash",
        generation_config={
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
    )
    response = model.generate_content(SYSTEM_PROMPT + "\n\nText:\n" + text[:4000])
    return json.loads(response.text.strip())

if __name__ == "__main__":
    print(f"\n📂 Scanning all files in: {DATA_DIR}")
    for file in os.listdir(DATA_DIR):
        fpath = os.path.join(DATA_DIR, file)
        if not os.path.isfile(fpath):
            continue

        print(f"\n🔍 Processing and routing: {file}")
        try:
            # 1️⃣ Extract text first (works for both images & text files)
            text = extract_text(fpath)
            if not text.strip():
                print(f"[Router Agent] ⚠️ No text extracted from {file}, skipping.")
                continue

            # 2️⃣ Route text to correct agent
            result = route_text(text)
            print(json.dumps(result, indent=2))

        except Exception as e:
            print(f"[Router Agent] ❌ Failed on {file}: {e}")
