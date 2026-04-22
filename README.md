# Week 1 — LangGraph: from primitives to production tool-use

6h code + 2h source reading + 2h LeetCode/review per day. Start from source code, not tutorials.

---

## Day 1 — StateGraph internals: understand, not just use

**Goal:** Read how LangGraph actually works before writing a single line that uses it.

### What was built

- Read `langgraph/graph/state.py` — traced how `_compile()` wires nodes and edges, and how state merges work (`operator.add` on `Annotated` fields vs plain overwrites)
- Built a pure state machine (no LLM): 3 nodes, 2 conditional edges, counter stops at 5
- Added `SqliteSaver`, killed the process mid-run, verified checkpoint recovery on restart
- LeetCode: Two Sum — O(n) with a hash map, one pass

### Key questions answered

**How does LangGraph merge state?**
Each node returns a partial dict. LangGraph calls the reducer for each key — if the type annotation is `Annotated[list, operator.add]`, the lists are concatenated; if it's a plain type, the value is overwritten. The merge happens in `_apply_writes()` inside the compiled graph.

**What does `_compile()` actually do?**
It validates that all edges reference real nodes, builds the execution order, wires the checkpointer into each step, and returns a `CompiledGraph` — which is what you actually call `.invoke()` or `.stream()` on. The `StateGraph` you build is just a blueprint.

### Files
| File | Description |
|---|---|
| `Day01/state_machine.py` | 3-node conditional graph, counter stops at 5 |
| `Day01/checkpoint_machine.py` | Same graph with `SqliteSaver`, simulated slow nodes |

---

## Day 2 — Command object vs conditional edges: know the boundary

**Goal:** Understand when each routing mechanism applies, not just how to use them.

### What was built

- Implemented the same routing logic two ways: `add_conditional_edges` and `Command`
- Found the scenario where only `Command` works: cross-subgraph jumps (`Command.PARENT`)
- Migrated a RAG retrieval node into LangGraph with fallback routing when results are empty
- Added full RAG + HITL with confidence-based routing and PostgreSQL checkpointer

### When to use `add_conditional_edges`
- Routing logic is a pure function of state
- Multiple nodes share the same routing logic — write once, reuse
- You want graph structure visible at definition time (useful for visualization)

### When to use `Command`
- Routing depends on what happened *inside* the node (computed result, not just state)
- You need to jump from a subgraph node back to the parent graph — `add_conditional_edges` cannot cross graph boundaries
- You want to update state *and* route in a single return value

### Key limitation
When using `Command.PARENT` to exit a subgraph, only the exiting node's state update propagates to the parent. Workaround: accumulate all updates in the final node before jumping.

### Files
| File | Description |
|---|---|
| `Day02/command_demo.py` | Same routing logic: `add_conditional_edges` vs `Command` |
| `Day02/subgraph_demo.py` | Cross-subgraph jump with `Command.PARENT` |
| `Day02/rag_graph.py` | RAG retrieval with fallback routing |
| `Day02/rag_hitl.py` | RAG + confidence-based HITL with PostgreSQL checkpointer |

---

## Day 3 — Real tool-use: side effects, errors, production error handling

**Goal:** Build agents that interact with the real world — filesystem, HTTP, subprocess — and handle failures gracefully in the graph layer.

### What was built

- **File tool** — read/write local files with error capture in state (not raised exceptions)
- **GitHub tool** — fetch repo issues via REST API, handles 403, timeouts, rate limits
- **Code executor** — run Python snippets via `subprocess` with 5s timeout and sandboxing notes
- **Error handling pattern** — dedicated error node, retry counter in state, up to 3 retries, then graceful degradation
- **Unified agent** — single graph that routes to all three tools based on `state["task"]`

### Key design decisions

**Why capture errors in state rather than raising?**
Raising an exception terminates the graph immediately. Storing the error in `state["error"]` lets downstream nodes — retry logic, fallback, human review — respond to the failure. This is the only approach that keeps the agent running and observable.

**Why `Command` for the router node?**
Task type could require parsing or classification logic inside the node. `Command` lets the node own the routing decision rather than exposing it at graph-definition time.

### Files
| File | Description |
|---|---|
| `Day03/file_tool.py` | File read/write graph with error handling |
| `Day03/code_executor.py` | Subprocess code runner with retry logic |
| `Day03/github_tool.py` | GitHub Issues API client graph |
| `Day03/agent.py` | Unified router dispatching to all three tools |

---

## Day 4 — (Skipped)

In folder day2
---

## Day 5 — Human-in-the-loop + persistence: async pause and resume

**Goal:** Build a HITL workflow where the agent truly exits the process and resumes later — not a blocking `input()` call.

### What was built

- `interrupt()` pause: agent snapshots state to PostgreSQL and exits the process
- Replaced `MemorySaver` with `PostgresSaver` (local Docker), verified state persists across restarts
- Time travel: `get_state_history()` to list checkpoints, branch to a new thread from any past state
- RAG integration: human review triggered when retrieval confidence falls below 0.6

### Three-file execution model

| File | Purpose |
|---|---|
| `run_first.py` | Start the graph, run until interrupt, inspect paused state |
| `run_resume.py` | Load the same `thread_id`, resume with `Command(resume=...)` |
| `time_travel.py` | Walk checkpoint history, branch to a new thread from any past checkpoint |

This split proves that graph state truly persists across process boundaries — the PostgreSQL checkpointer is the only connection between the two runs.

### How `interrupt()` actually works
`interrupt()` is not a pause — it is a **state snapshot followed by a clean exit**. Everything is already saved to the checkpointer when the exception is raised. Resuming is just a new `graph.stream()` call with the same `thread_id` and `Command(resume=...)` as input.

### Time travel mechanics
1. `graph.get_state_history(config)` — list all checkpoints for a thread
2. Find the snapshot where `next == ("human_review",)` — the interrupt point
3. Create a new `thread_id` (branch)
4. `graph.update_state(branch_config, target.values, as_node="human_review")` — inject historical state
5. Override `human_decision` and stream from there

### Files
| File | Description |
|---|---|
| `Day05/graph.py` | HITL graph with confidence-based routing and PostgreSQL checkpointer |
| `Day05/run_first.py` | Initial run, stops at interrupt |
| `Day05/run_resume.py` | Resumes from interrupt with human approval |
| `Day05/time_travel.py` | Branches from a past checkpoint with a different decision |

---

## Day 6 — RAG + HITL: production wiring

**Goal:** Wire the full RAG pipeline into LangGraph with confidence-based human review and PostgreSQL persistence.

> Day 6 content is documented in [Day02/README.md](Day02/README.md) — the RAG + HITL implementation was developed as an extension of Day 2's routing patterns.

### Architecture
```
retrieve → confidence ≥ 0.7 → generate → END
         → confidence < 0.7 → human_review → generate → END
         → no results       → fallback → END
```

### Why 0.7 as the confidence threshold?
Tested with real queries — high relevance scores cluster above 0.8, unrelated queries score below 0.65. 0.7 gives a clean separation with the test document set.

---

## Day 7 — Week 1 wrap-up: RAG migrated to LangGraph + Streamlit UI

**Goal:** Rewrite the RAG project from LCEL to `StateGraph`, add streaming, and build a real UI.

### What was built

- Full RAG pipeline rewritten as `StateGraph` — retrieve, confidence route, human review, generate, fallback
- `stream_mode=["updates", "messages"]` dual-mode streaming: node completion events + LLM token chunks simultaneously
- Streamlit UI: chat input, real-time token streaming, interrupt-aware review panel with Approve/Reject

### LCEL chain vs LangGraph StateGraph

| | LCEL Chain | LangGraph StateGraph |
|---|---|---|
| Control flow | Linear pipe, branching via `RunnableBranch` | Explicit nodes and edges, arbitrary graph topology |
| Human-in-the-loop | Not supported natively | `interrupt()` — process exits, resumes from checkpointer |
| State persistence | No built-in persistence | PostgreSQL / SQLite checkpointer, survives restarts |
| Error handling | Exception propagates up the chain | Route to error node, retry counter in state |
| Observability | Step-level via LangSmith | Node-level events via `stream_mode="updates"` |
| Streaming | Token streaming via `.stream()` | Token + event streaming via dual `stream_mode` |
| Best for | Simple linear RAG, prototypes | Production agents, HITL, long-running workflows |

### Dual stream mode
```python
graph.stream(..., stream_mode=["updates", "messages"])
```
- `"updates"` — catches `__interrupt__` events and node completion (status box)
- `"messages"` — streams LLM token chunks as they arrive (live answer display)

Both in one loop — the only way to get real-time streaming *and* interrupt detection simultaneously.

### Files
| File | Description |
|---|---|
| `Day07/rag_graph.py` | StateGraph RAG with streaming LLM and PostgreSQL checkpointer |
| `Day07/rag_hitl.py` | Standalone test script (non-streaming, with test queries) |
| `Day07/app.py` | Streamlit UI |

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt  # or: uv sync

# Copy and fill in secrets
cp .env.example .env

# Start PostgreSQL (required for Day 5-7)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password -e POSTGRES_DB=checkpoints postgres

# Run Streamlit UI (Day 7)
cd Day07 && streamlit run app.py
```

### Environment variables (`.env`)
```
OPENAI_API_KEY=...
GITHUB_TOKEN=...
DATABASE_URL=postgresql://postgres:password@localhost:5432/checkpoints
```

---

## Stack

- [LangGraph](https://github.com/langchain-ai/langgraph) — agent orchestration
- [LangChain](https://github.com/langchain-ai/langchain) — LLM + embeddings
- [Chroma](https://www.trychroma.com/) — vector store
- [OpenAI](https://platform.openai.com/) — `gpt-4o-mini` + embeddings
- [PostgreSQL](https://www.postgresql.org/) — checkpoint persistence
- [Streamlit](https://streamlit.io/) — UI
