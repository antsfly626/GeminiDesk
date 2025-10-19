import os
from google import genai
import json

class APIClient:
    def __init__(self, api_key=None, api_base=None, ws_url=None):
        """
        Initializes the Gemini client and optional URLs for your backend.
        """
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.api_base = api_base or "http://127.0.0.1:8000"
        self.ws_url = ws_url or "ws://127.0.0.1:8000/ws/logs"

    def generate_text(self, prompt: str) -> str:
        """
        Sends a text prompt to Gemini 2.5-flash and returns raw text.
        """
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text

    def generate_json(self, prompt: str) -> dict:
        """
        Sends a prompt expecting structured JSON and parses the result.
        """
        response_text = self.generate_text(prompt)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": response_text}


class MockStream:
    def __init__(self, logs_queue, router_signal):
        self.logs_queue = logs_queue
        self.router_signal = router_signal

    async def autorun(self):
        import asyncio
        # just simulate logs for testing
        while True:
            await self.logs_queue.put("Mock log entry")
            await asyncio.sleep(1)
