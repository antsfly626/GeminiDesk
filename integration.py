# integration.py
import os
import json
from app.agents.ocr_agent import extract_text
from app.agents.router_agent import route_text
from app.agents.cal_agent import parse_with_gemini, create_calendar_event

# ✅ Ensure correct base directory
BASE_DIR = os.path.dirname(__file__)

# DATA_DIR = os.path.join(BASE_DIR, "data", "finance")
# test_file = os.path.join(DATA_DIR, "boba_reciept.jpg")

# DATA_DIR = os.path.join(BASE_DIR, "data", "events")
# test_file = os.path.join(DATA_DIR, "pinterest_trip.txt")

DATA_DIR = os.path.join(BASE_DIR, "data", "notes")
test_file = os.path.join(DATA_DIR, "cse130_note.jpg")

print(BASE_DIR)
print(f"🔍 File: {test_file}")
print(f"📂 Exists? {os.path.exists(test_file)}")

if not os.path.exists(test_file):
    raise FileNotFoundError(f"❌ Missing test file: {test_file}")

# 1️⃣ OCR Extraction
print("\n🧠 Extracting text...")
text = extract_text(test_file)
print(f"📜 Extracted text ({len(text)} chars): {text[:400]}...\n")

# 2️⃣ Route to correct agent
print("🤖 Routing text to correct agent...")
routing = route_text(text)
print("🔎 Router decision:", json.dumps(routing, indent=2))

# 3️⃣ Dispatch to the appropriate agent
agent = routing["agent"]

if agent == "EventAgent":
    print("\n📅 Detected event! Sending to Calendar Agent...")
    parsed = parse_with_gemini(text)
    print(json.dumps(parsed, indent=2))
    try:
        link = create_calendar_event(parsed, port=8083)
        print("✅ Calendar event created:", link)
    except Exception as e:
        print("❌ Calendar creation failed:", e)

elif agent == "TaskAgent":
    print("\n🗓️ Detected task! (You can connect your Notion Task agent here later.)")

elif agent == "NoteAgent":
    print("\n📝 Detected note/document. Would be saved in Notes system.")

elif agent == "FinanceAgent":
    print("\n💰 Detected finance/receipt. Sending to Fetch.ai Finance Agent...")
    from app.agents.fetch_finance_agent import call_fetch_finance_agent
    import asyncio

    parsed = asyncio.run(call_fetch_finance_agent(text))
    print(json.dumps(parsed, indent=2))

else:
    print("\n🤷 Unknown agent. Router confidence too low.")
