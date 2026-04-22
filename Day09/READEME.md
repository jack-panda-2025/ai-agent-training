# Day 9 — Swarm Pattern

## What this does
The same task as Day 8 (article URL → summary + Chinese translation)
implemented using the Swarm pattern instead of Supervisor.

## Task
Given a tech article URL:
1. Fetch and parse the article (fetcher)
2. Summarize into 3-5 bullet points (summarizer)
3. Translate summary to Chinese (translator)

## How it works
Each agent decides who runs next via Command object.
No central supervisor — peer-to-peer handoff.

## Supervisor vs Swarm — Comparison

### Same task
Given a tech article URL → summary + Chinese translation

### LLM calls
| | Supervisor | Swarm |
|---|---|---|
| Routing calls | 4 (one per step + FINISH check) | 0 |
| Worker LLM calls | 2 (summarizer + translator) | 2 (summarizer + translator) |
| Total | 6 | 2 |

### When I would choose Supervisor
- Task has conditional branching (e.g. "translate only if article is English")
- Need failure recovery (retry fetcher, trigger human review)
- Adding new workers frequently — only change prompt, not graph structure

### When I would choose Swarm
- Task is strictly sequential with no branching
- Token cost matters
- Each worker always knows its successor

### The core tradeoff
Supervisor: resilient, observable, expensive
Swarm: fast, cheap, fragile on failure