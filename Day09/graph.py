from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from state import AgentState
from workers import fetcher_node, summarizer_node, translator_node
import psycopg
import os


def build_graph():
    DB_URI = "postgresql://localhost:5432/langgraph_checkpoints"

    builder = StateGraph(AgentState)

    builder.add_node("fetcher", fetcher_node)
    builder.add_node("summarizer", summarizer_node)
    builder.add_node("translator", translator_node)

    # Entry point: always start at supervisor
    builder.set_entry_point("fetcher")
    return builder


def get_graph():
    DB_URI = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/checkpoints"
    )
    conn = psycopg.connect(DB_URI, autocommit=True)
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
    return build_graph().compile(checkpointer=checkpointer)
