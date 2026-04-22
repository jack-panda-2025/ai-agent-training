from server import mcp

if __name__ == "__main__":
    print("Starting MCP server at http://127.0.0.1:8000/mcp")
    mcp.run(transport="streamable-http")
