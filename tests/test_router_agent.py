import json
from app.agents import router_agent

def test_router_agent():
    sample_path = "data/pinterest_trip.txt"
    with open(sample_path, "r", encoding="utf-8") as f:
        text = f.read()
    result = router_agent.route_text(text)

    print("\n🔍 RouterAgent output:")
    print(json.dumps(result, indent=2))

    # Optional: basic validation
    assert "agent" in result
    assert "confidence" in result
    assert "content" in result