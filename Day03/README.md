# Day 3 — Tool Use: File I/O, Code Execution, and GitHub API

## What changed from Day 2

Day 2 explored routing patterns within a graph. Day 3 adds real-world **tool nodes** — nodes that interact with external systems (filesystem, subprocess, GitHub API). Each tool is isolated in its own file and graph.

## Tools built

### `file_tool.py` — File read/write agent
Nodes: `write_file` → `read_file` → `verify`

The agent writes content to disk, reads it back, and verifies the round-trip. Errors at any step are captured in state and surfaced rather than raised as exceptions — this keeps the graph running and makes the failure observable.

### `code_executor.py` — Python code execution agent
Nodes: `execute_code` → (success: END) or (error: `fix_code` → retry)

Runs arbitrary Python via `subprocess`. Uses a 5-second timeout to prevent runaway code. On failure, routes to a `fix_code` node that attempts a correction, then retries up to a configurable limit tracked in `state["retries"]`.

### `github_tool.py` — GitHub Issues fetcher
Nodes: `fetch_issues` → `format_output`

Calls the GitHub REST API with a personal token. Handles 403 (rate-limit / auth failure) and network errors explicitly. Issues are stored as a list in state, then formatted for display.

### `agent.py` — Unified multi-tool agent
A single graph that routes to the appropriate tool subgraph based on `state["task"]`. The router reads the task type and issues a `Command(goto=...)` to the correct entry point.

## Key design decisions

**Why `Command` instead of `add_conditional_edges` for the router?**
The task type is determined inside the router node (could involve parsing, LLM classification, etc.) — not purely derivable from state at graph-definition time. `Command` lets the node own the routing decision.

**Why capture errors in state rather than raising?**
Raising an exception terminates the graph. Storing the error in state lets downstream nodes (retry logic, fallback nodes, human review) respond to the failure. This is essential for resilient agents.

**Security note:** GitHub tokens are hardcoded in these files for local learning purposes. In production, use environment variables or a secrets manager.

## Code structure
- `file_tool.py` — isolated file read/write graph with error handling
- `code_executor.py` — subprocess-based code runner with retry logic
- `github_tool.py` — GitHub Issues API client graph
- `agent.py` — unified router that dispatches to all three tools
