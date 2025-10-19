import os
import json
from google import genai

class RouterAgent:
    def __init__(self, api_key=None):
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))

    def classify_document(self, image_path: str) -> dict:
        """
        Sends the image to Gemini and returns structured JSON:
        {
          "agent": "<AgentName>",
          "confidence": <float between 0 and 1>,
          "content": "<short description of text>"
        }
        """
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

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"file_data": {"mime_type": "image/jpeg", "file_uri": f"file:///{image_path}"}}
                ]
            }]
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": response.text}
