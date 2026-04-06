import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import interrupt
from typing import TypedDict, Annotated
from psycopg import Connection
import operator


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    retrieval_confidence: float
    human_decision: str
    result: str


def retrieve_node(state: AgentState):
    print("Retrieving...")
    return {"messages": ["retrieval done"], "retrieval_confidence": 0.45}


def route_after_retrieve(state: AgentState):
    if state["retrieval_confidence"] < 0.6:
        return "need_review"
    return "auto_proceed"


def human_review_node(state: AgentState):
    print(
        f"Confidence {state['retrieval_confidence']:.2f} is low, pausing for human review..."
    )
    decision = interrupt(
        {
            "question": "Retrieval confidence is low. Approve or reject?",
            "confidence": state["retrieval_confidence"],
        }
    )
    return {"human_decision": decision}


def generate_node(state: AgentState):
    decision = state.get("human_decision", "auto")
    if decision == "reject":
        return {"result": "rejected by human, pipeline stopped"}
    return {"result": f"Generation complete. (Decision):{decision}"}


builder = StateGraph(AgentState)
builder.add_node("retrieve", retrieve_node)
builder.add_node("human_review", human_review_node)
builder.add_node("generate", generate_node)

builder.add_edge(START, "retrieve")
builder.add_conditional_edges(
    "retrieve",
    route_after_retrieve,
    {"need_review": "human_review", "auto_proceed": "generate"},
)
builder.add_edge("human_review", "generate")
builder.add_edge("generate", END)

DB_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/checkpoints")
conn = Connection.connect(DB_URI, autocommit=True)
checkpointer = PostgresSaver(conn)
checkpointer.setup()
graph = builder.compile(checkpointer=checkpointer)
