from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"


async def get_agent():
    client = MultiServerMCPClient(
        {"week2-server": {"url": MCP_SERVER_URL, "transport": "streamable_http"}}
    )
    tools = await client.get_tools()

    print(f"[agent] Got {len(tools)} tools:")
    for tool in tools:
        print(f" - {tool.name}")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_react_agent(llm, tools)
    return agent, client
