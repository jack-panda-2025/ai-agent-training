from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from state import AgentState
from workers import fetcher_node, summarizer_node, translator_node
from supervisor import supervisor_node, route_after_supervisor, WORKERS
import psycopg
import os

DB_URI = "postgresql://localhost:5432/langgraph_checkpoints"


def build_graph():
    builder = StateGraph(AgentState)

    # Add all nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("fetcher", fetcher_node)
    builder.add_node("summarizer", summarizer_node)
    builder.add_node("translator", translator_node)

    # Entry point: always start at supervisor
    builder.set_entry_point("supervisor")

    # THE key edge: supervisor has a conditional edge to all workers + END
    # route_after_supervisor reads state["next"] and returns the node name
    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "fetcher": "fetcher",
            "summarizer": "summarizer",
            "translator": "translator",
            "FINISH": END,
        },
    )

    # All workers return to supervisor — this is what makes it a supervisor pattern
    for worker in WORKERS:
        builder.add_edge(worker, "supervisor")

    return builder


def get_graph():
    DB_URI = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/checkpoints"
    )
    conn = psycopg.connect(DB_URI, autocommit=True)
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
    graph = build_graph().compile(checkpointer=checkpointer)
    return graph
