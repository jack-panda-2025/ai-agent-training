import asyncio
from agent import get_agent
from langchain_core.messages import HumanMessage


async def run(task: str):
    agent, client = await get_agent()
    result = await agent.ainvoke({"messages": [HumanMessage(content=task)]})

    for message in result["messages"]:
        role = message.__class__.__name__
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                print(f"[tool call] {tc['name']}({tc['args']})")
        elif hasattr(message, "content") and message.content:
            print(f"[{role}] {message.content[:300]}")


if __name__ == "__main__":
    asyncio.run(
        run(
            "Search the knowledge base for information about "
            "LangGraph checkpointers and save the answer to output/rag_result.md"
        )
    )
