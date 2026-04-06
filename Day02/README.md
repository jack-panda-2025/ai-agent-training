# Day 2 — Command vs Conditional Edges

## When to use `add_conditional_edges`
- When routing logic is simple and can be expressed as a pure function of state
- When you want graph structure to be visible at the graph definition level
- When multiple nodes share the same routing logic — write once, reuse

## When to use `Command`
- When routing logic depends on what happened inside the node
- When you need to jump out of a subgraph to the parent graph — `add_conditional_edges` cannot do this

## Key limitation discovered
When using `Command.PARENT` to exit a subgraph, only the exiting node's
state update is propagated back to the parent graph. Workaround: combine
all necessary updates in the final node before jumping.

## Day 6 Addition — RAG + HITL with confidence-based routing

### Architecture
retrieve → confidence > 0.7 → generate
→ confidence < 0.7 → human_review → generate
→ no results       → fallback

### Key design decisions

**Why confidence threshold at 0.7?**
Tested with real queries — high relevance scores cluster above 0.8,
unrelated queries score below 0.65. 0.7 gives a clean separation.

**Why interrupt() instead of input()?**
`input()` blocks the process. `interrupt()` saves state to PostgreSQL
and exits — the process can restart days later and resume from the
exact same point. This is the only viable approach in production.

**What the human reviewer sees**
The interrupt payload includes: confidence score, retrieved documents,
and the original query. This gives the reviewer enough context to decide
whether the retrieval is trustworthy.

## Code structure
- `command_demo.py` — same routing logic two ways
- `subgraph_demo.py` — cross-subgraph jump with Command.PARENT
- `rag_graph.py` — RAG retrieval with fallback routing
- `rag_hitl.py` — RAG + confidence-based HITL with PostgreSQL checkpointer

## How this system can fail
- Confidence threshold is fixed at 0.7 — may need tuning per domain
- Human reviewer sees low-quality documents but may still approve
- PostgreSQL connection failure means checkpoints cannot be saved