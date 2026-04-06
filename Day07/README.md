# Day 7 — Streamlit UI for RAG + HITL Agent

## What this adds

Day 5/6 implemented the RAG + HITL graph as a backend. Day 7 wraps it in a **Streamlit web UI**, turning the terminal-based interrupt workflow into a real interactive chat application.

## Architecture

```
User types query
    ↓
app.py: graph.stream(..., stream_mode=["updates", "messages"])
    ↓
confidence ≥ 0.7 → tokens stream to chat window → Done
confidence < 0.7 → interrupt fires → UI switches to review mode
    ↓ (human clicks Approve/Reject)
graph.stream(Command(resume=...), ...) → answer streams → Done
```

## Streamlit state management

The UI tracks three pieces of session state:
- `thread_id` — a fresh UUID per query, identifies the PostgreSQL checkpoint
- `is_waiting` — boolean that switches the UI between "chat input" mode and "review" mode
- `interrupt_payload` — the dict passed to `interrupt()`, displayed to the reviewer

When `is_waiting=True`, the chat input is hidden and replaced with the review panel showing confidence score, the original query, and the retrieved documents.

## Dual stream mode

```python
graph.stream(..., stream_mode=["updates", "messages"])
```

Using both modes simultaneously:
- `"updates"` — catches `__interrupt__` events and node completion signals (used for the status box)
- `"messages"` — streams LLM token chunks as they arrive (used for the live answer display)

This is the only way to get both real-time token streaming *and* interrupt detection in the same event loop.

## How the resume works from Streamlit

Streamlit re-renders on every button click. The Approve/Reject buttons:
1. Read `thread_id` from session state (the same thread that was interrupted)
2. Call `graph.stream(Command(resume="approve"/"reject"), config=config)`
3. Set `is_waiting = False`
4. Call `st.rerun()` to trigger a clean re-render with the answer in chat history

## Code structure
- `rag_graph.py` — RAG graph with confidence routing, HITL interrupt, and PostgreSQL checkpointer (streaming-enabled LLM)
- `rag_hitl.py` — standalone test script for the same graph (non-streaming, with test queries)
- `app.py` — Streamlit UI

## Running

```bash
streamlit run app.py
```

Requires PostgreSQL running at `localhost:5432` with a `checkpoints` database.
