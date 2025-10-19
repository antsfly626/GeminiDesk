# app/agents/fetch_finance_agent.py
import os, json, httpx, asyncio
from dotenv import load_dotenv

load_dotenv()

FETCH_API_KEY = os.getenv("FETCH_API_KEY")
FETCH_FINANCE_AGENT_ADDRESS = os.getenv("FETCH_FINANCE_AGENT_ADDRESS")

async def call_fetch_finance_agent(text: str):
    """Send text (like a receipt) to a Fetch.ai Finance Agent via Agentverse API."""
    if not FETCH_API_KEY:
        return {"error": "Missing FETCH_API_KEY — add it to your .env"}
    if not FETCH_FINANCE_AGENT_ADDRESS:
        return {"error": "Missing FETCH_FINANCE_AGENT_ADDRESS — add it to your .env"}

    # ✅ correct authenticated API endpoint
    url = f"https://api.agentverse.ai/v1/agents/{FETCH_FINANCE_AGENT_ADDRESS}/interact"

    headers = {
        "Authorization": f"Bearer {FETCH_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "protocol": "AgentChatProtocol",
        "version": "0.3.0",
        "input": {
            "type": "text",
            "data": text
        }
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code != 200:
                return {"error": f"HTTP {r.status_code}: {r.text}"}
            return r.json()
    except Exception as e:
        return {"error": str(e)}
