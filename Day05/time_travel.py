from graph import graph
from langgraph.types import Command
import uuid

config = {"configurable": {"thread_id": "session_001"}}

# Step 1: 查看历史
print("=== Checkpoint History ===")
history = list(graph.get_state_history(config))
for i, snapshot in enumerate(history):
    print(f"[{i}] next={snapshot.next}")
    print(
        f"     checkpoint_id={snapshot.config['configurable']['checkpoint_id'][:8]}..."
    )
    print()

# Step 2: 找到 interrupt 发生的 checkpoint
target = None
for snapshot in history:
    if snapshot.next == ("human_review",):
        target = snapshot
        break

if not target:
    print("No interrupt checkpoint found")
else:
    print(
        f"Found interrupt checkpoint: {target.config['configurable']['checkpoint_id'][:8]}..."
    )

    # Step 3: 创建新 thread，注入状态，指定从 human_review 开始
    branch_config = {
        "configurable": {"thread_id": f"session_001_branch_{uuid.uuid4().hex[:6]}"}
    }

    graph.update_state(branch_config, target.values, as_node="human_review")

    # directly set the human decision in state
    graph.update_state(
        branch_config, {"human_decision": "reject"}, as_node="human_review"
    )

    print(f"Branching into new thread: {branch_config['configurable']['thread_id']}")

    print("\n=== Re-running with reject ===")
    for event in graph.stream(None, config=branch_config, stream_mode="updates"):
        print(f"Event: {event}")

    final = graph.get_state(branch_config)
    print(f"\nFinal result: {final.values['result']}")
