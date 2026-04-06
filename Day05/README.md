# Day 5 — Human-in-the-Loop and Time Travel

## What this builds on

Day 2 introduced `interrupt()` conceptually. Day 5 implements a full HITL workflow with PostgreSQL persistence, then adds **time travel** — the ability to replay execution from any past checkpoint.

## Graph architecture (`graph.py`)

```
retrieve → (confidence ≥ 0.6) → generate → END
         → (confidence < 0.6) → human_review → generate → END
```

`retrieve_node` simulates a low-confidence result (0.45) to force the human review path. `human_review_node` calls `interrupt()` with a payload containing the question and confidence score.

## Three-file execution model

The workflow is split across three scripts to simulate real-world multi-process operation:

| File | Purpose |
|---|---|
| `run_first.py` | Start the graph, run until interrupt, print paused state |
| `run_resume.py` | Load the same `thread_id`, resume with `Command(resume=...)` |
| `time_travel.py` | Walk checkpoint history, branch to a new thread from any past state |

This split is deliberate — it proves that the graph state truly persists across process boundaries. The PostgreSQL checkpointer is the only thing connecting the two runs.

## Time travel mechanics (`time_travel.py`)

1. Call `graph.get_state_history(config)` to list all checkpoints for a thread.
2. Find the snapshot where `next == ("human_review",)` — the interrupt point.
3. Create a new `thread_id` (branch).
4. Call `graph.update_state(branch_config, target.values, as_node="human_review")` to inject the historical state into the new thread.
5. Override `human_decision` and stream from there.

This lets you re-run any decision point with a different human response without modifying the original thread.

## Key insight

`interrupt()` is not a pause — it is a **state snapshot followed by a clean exit**. The graph has already saved everything to the checkpointer. Resuming is just starting a new `graph.stream()` call with the same `thread_id` and a `Command(resume=...)` as input.

## Code structure
- `graph.py` — graph definition with confidence-based HITL routing
- `run_first.py` — initial run, stops at interrupt
- `run_resume.py` — resumes from interrupt with human approval
- `time_travel.py` — branches from a past checkpoint with a different decision
