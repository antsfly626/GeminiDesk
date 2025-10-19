import httpx, json, asyncio

from app.agents.fetch_finance_agent import call_fetch_finance_agent

async def test():
    text = "Boba & Brew receipt — Lychee $6.25, Tax $0.54, Total $6.79"
    resp = await call_fetch_finance_agent(text)
    print(json.dumps(resp, indent=2))

asyncio.run(test())
