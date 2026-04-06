from graph import graph
from langgraph.types import Command

config = {"configurable": {"thread_id": "session_001"}}

state = graph.get_state(config)
print(f"Resuming from: {state.next}")

print("\n=== New process, human approved, resuming ===")
for event in graph.stream(
    Command(resume="approve"), config=config, stream_mode="updates"
):
    print(f"Event: {event}")

final = graph.get_state(config)
print(f"\nFinal result: {final.values['result']}")
