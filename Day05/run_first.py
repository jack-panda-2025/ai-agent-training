from graph import graph

config = {"configurable": {"thread_id": "session_001"}}

print("=== First run ===")
for event in graph.stream(
    {
        "messages": [],
        "retrieval_confidence": 0.0,
        "human_decision": "",
        "result": "",
    },
    config=config,
    stream_node="updates",
):
    print("Event:", event)

state = graph.get_state(config=config)
print(f"\nGraph is paused at: {state.next}")
print(f"\n Interrupt payload: {state.tasks}")

# from langgraph.types import Command

# print("\n=== Resuming with human decision ===")
# for event in graph.stream(
#     Command(resume="reject"),
#     config=config,
#     stream_node="updates",
# ):
#     print("Event:", event)

# final = graph.get_state(config=config)
# print(f"\nFinal result: {final.values['result']}")
