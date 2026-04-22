# Day 12 — LangGraph Agent + MCP Client

## What this does
A LangGraph ReAct agent that connects to the Day 11 MCP server
and uses its tools to complete a multi-step task.

## Task
"Search the knowledge base for information about LangGraph 
checkpointers and save the answer to output/rag_result.md"

## How it works
1. Agent connects to MCP server at http://127.0.0.1:8000/mcp
2. Fetches tool list — discovers query_rag, write_file, github_issues
3. LLM reasons about task → decides tool order → executes

## Observed execution
[HumanMessage] Search the knowledge base...
[tool call] query_rag({'query': 'LangGraph checkpointers'})
[ToolMessage] No relevant documents found.
[tool call] write_file({'filename': 'output/rag_result.md', ...})
[ToolMessage] Successfully wrote 64 characters
[AIMessage] Searched KB, found nothing, saved result to file.

## Key design decisions

### Why create_react_agent instead of building graph manually?
ReAct handles the reasoning loop automatically — no need to define
nodes, edges, or routing logic. Trade flexibility for speed.
Supervisor pattern is better when task order must be guaranteed.

### Why MultiServerMCPClient?
Supports connecting to multiple MCP servers simultaneously.
Agent sees all tools from all servers as one unified list.
Useful in Week 3 when multiple specialized servers are needed.

### Can the agent always call tools in the right order?
No. Order depends on LLM reasoning, task description clarity,
and tool description quality. ReAct has no hardcoded sequence.
Supervisor pattern is more reliable for complex ordered tasks.

## How to run
# Terminal 1 — start MCP server
cd ../day11_mcp_server && python main.py

# Terminal 2 — run agent
python main.py

## Tech stack
- LangGraph create_react_agent
- langchain-mcp-adapters MultiServerMCPClient
- MCP Streamable HTTP transport