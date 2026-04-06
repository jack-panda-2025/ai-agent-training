# Day 1 — LangGraph Basics: State, Nodes, and Checkpoints

## Core concepts

**State** is a `TypedDict` that flows through the graph. The `Annotated[list, operator.add]` pattern means list fields are *appended* rather than overwritten on each update — this is how you accumulate history.

**Nodes** are plain Python functions that receive the current state and return a partial update dict. LangGraph merges the update into the existing state.

**Conditional edges** route execution based on a function of the current state. The routing function returns a string matching a node name or `END`.

## Graph architecture in `state_machine.py`

```
node_a → (even counter) → node_b → node_a → ...
       → (odd counter)  → node_c → node_a → ...
       → (counter ≥ 5)  → END
```

Three nodes cycle until `counter >= 5`. The routing logic lives in separate functions (`route_from_a`, `route_from_b`, `route_from_c`), not inside the nodes — this keeps nodes pure.

## Checkpointing in `checkpoint_machine.py`

`SqliteSaver` persists the graph state to a local `.db` file after every node execution. This means:
- The process can be killed mid-run and resumed from the last completed node.
- `thread_id` in `configurable` identifies a specific run — different thread IDs are independent execution histories.

`time.sleep(5)` is used to simulate slow nodes, making it easy to observe the checkpoint-then-resume behavior.

## Key insight

Checkpointing is not optional in production agents — it is what separates a script that runs once from an agent that can pause, resume, and recover from failures.

## Code structure
- `state_machine.py` — basic conditional routing with three nodes
- `checkpoint_machine.py` — same pattern with SQLite checkpointer and simulated slow nodes
- `checkpoint.db` — SQLite file generated at runtime (not committed)
