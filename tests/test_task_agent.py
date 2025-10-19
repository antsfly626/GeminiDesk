# app/tests/test_task_agent.py
from app.agents.task_agent import analyze_task

def test_task_agent():
    with open("data/todo_meeting.txt", "r") as f:
        text = f.read()
    result = analyze_task(text)
    print("\n✅ TaskAgent output:")
    print(result)
