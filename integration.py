# integration.py
import os
import json
import asyncio

from app.agents.ocr_agent import extract_text               # OCR for router
from app.agents.router_agent import route_text              # Router
from app.agents.cal_agent import parse_with_gemini, create_calendar_event
from app.agents.task_agent import parse as parse_task       # Task Agent
from app.agents.note_agent import run_note_agent # Note Agent

BASE_DIR = os.path.dirname(__file__)

DATA_DIR = os.path.join(BASE_DIR, "data", "notes")
test_file = os.path.join(DATA_DIR, "cse130_note.jpg")

print(BASE_DIR)
print(f"🔍 File: {test_file}")
print(f"📂 Exists? {os.path.exists(test_file)}")

if not os.path.exists(test_file):
    raise FileNotFoundError(f"❌ Missing test file: {test_file}")

print("\n🧠 Extracting text with OCR Agent...")
text = extract_text(test_file)
print(f"📜 Extracted text ({len(text)} chars): {text[:400]}...\n")

print("🤖 Routing text to correct agent...")
routing = route_text(text)
print("🔎 Router decision:", json.dumps(routing, indent=2))

agent = routing.get("agent", "")
confidence = routing.get("confidence", 0)

if not agent or confidence < 0.5:
    print("\n🤷 Unknown or low-confidence route. Skipping.")
    exit()

# 📅 Event Agent
if agent == "EventAgent":
    print("\n📅 Detected event! Sending to Calendar Agent...")
    parsed = parse_with_gemini(text)
    print(json.dumps(parsed, indent=2))
    try:
        link = create_calendar_event(parsed, port=8083)
        print("✅ Calendar event created:", link)
    except Exception as e:
        print("❌ Calendar creation failed:", e)

# 🗓️ Task Agent
elif agent == "TaskAgent":
    print("\n🗓️ Detected task! Sending to Task Agent...")
    try:
        result = asyncio.run(parse_task({"text": text}))
        print("✅ TaskAgent result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("❌ TaskAgent failed:", e)

# 📝 Note Agent
elif agent == "NoteAgent":
    print("\n📝 Detected note/document! Sending to NoteAgent (Notion Document Hub)...")
    try:
        result = run_note_agent(test_file, category="Planning")
        print("✅ NoteAgent uploaded document:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("❌ NoteAgent failed:", e)

# 💰 Finance Agent
elif agent == "FinanceAgent":
    print("\n💰 Detected finance/receipt. Would be processed by Finance Agent.")

else:
    print(f"\n🤷 Unknown agent type: {agent}")
