# Day 11 — MCP Server from Scratch

## What this does
A Model Context Protocol (MCP) server with 3 real tools,
built using FastMCP and Streamable HTTP transport.

## Tools

### query_rag
Searches a Chroma vector store knowledge base.
Returns top 3 relevant document chunks for a given query.

### write_file
Writes text content to a local file.
Creates parent directories automatically if they don't exist.

### github_issues
Fetches open issues from any public GitHub repository.
Handles rate limiting, timeouts, and 404 errors explicitly.

## MCP Handshake Sequence

Client (LangGraph Agent)          Server (FastMCP)
        |                                |
        |-- POST /mcp initialize ------->|
        |<-- session ID + capabilities --|
        |                                |
        |-- POST /mcp tools/list ------->|
        |<-- [query_rag, write_file, github_issues] --|
        |                                |
        |-- POST /mcp tools/call ------->|
        |   {name: "query_rag",          |
        |    arguments: {query: "..."}}  |
        |<-- tool result ----------------|
        |                                |
        |-- POST /mcp tools/call ------->|
        |   {name: "write_file", ...}    |
        |<-- tool result ----------------|
## Key design decisions

### Why Streamable HTTP, not stdio?
stdio requires client and server to run as the same process.
Streamable HTTP makes the server a real network endpoint —
any agent anywhere can connect to it. Production-ready.

### Why return str from every tool?
MCP tool results are sent over HTTP as JSON.
LangChain Document objects are not serializable.
LLM clients can only read text, not framework objects.
Always return primitives: str, int, bool, dict.

### Why tool descriptions matter
The LLM client never sees your implementation.
It only sees: tool name + description + parameter schema.
Description quality directly determines when the LLM calls
your tool. Vague description = wrong or missed tool calls.

### Why cap github_issues limit at 10?
Protect against accidentally fetching hundreds of issues
and blowing the LLM context window with irrelevant data.

## How to verify with curl

### Step 1 — initialize (get session ID)
```bash
curl -v -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

### Step 2 — list tools
```bash
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: YOUR-SESSION-ID" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}'
```

### Step 3 — call a tool
```bash
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: YOUR-SESSION-ID" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "github_issues",
      "arguments": {"repo": "langchain-ai/langgraph", "limit": 3}
    },
    "id": 3
  }'
```

## How to run
```bash
python main.py
# Server starts at http://127.0.0.1:8000/mcp
```

## Tech stack
- FastMCP (modelcontextprotocol/python-sdk)
- Streamable HTTP transport
- Chroma vector store
- httpx for GitHub API calls