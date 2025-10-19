import os
import json
from app.agents.cal_agent import parse_with_gemini, create_calendar_event

# Resolve input file relative to this test file
BASE_DIR = os.path.dirname(__file__)
file_path = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "events", "pinterest_trip.txt"))

print(f"🔍 Looking for file: {file_path}")
print(f"📂 Exists? {os.path.exists(file_path)}")
if not os.path.exists(file_path):
    raise FileNotFoundError(f"Expected file not found at: {file_path}")

# 1) Read free-form text
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# 2) Parse with Gemini
print("\n🤖 Parsing event text with Gemini...")
result = parse_with_gemini(text)
print(json.dumps(result, indent=2))

# 3) Create in Google Calendar (use a non-default OAuth port to avoid conflicts)
print("\n📅 Creating event on Google Calendar...")
try:
    link = create_calendar_event(result, port=8082)
    print("✅ Added to calendar:", link)
except Exception as e:
    print("❌ Failed to create event:", e)
