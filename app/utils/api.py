import os
from google import genai

# Use your environment variable key (since it works now)
client = genai.Client()

# Path to your test image
image_path = r"C:\Users\nehah\GeminiDesk\GeminiDesk\app\images\note.jpg"

# Create the structured classification prompt
prompt = """
You are a document classifier. 
Take an image and determine if it’s a handwritten note, a receipt, or a flyer.
Return structured JSON only in this format:
{
  "agent": "<AgentName>",
  "confidence": <float between 0 and 1>,
  "content": "<short description of text>"
}
"""

# Send image and prompt to Gemini
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        {"role": "user", "parts": [
            {"text": prompt},
            {"file_data": {"mime_type": "image/jpeg", "file_uri": f"file:///{image_path}"}}
        ]}
    ]
)

# Print the JSON output
print(response.text)
