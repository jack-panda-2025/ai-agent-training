import operator
from typing import Annotated, TypedDict


class State(TypedDict):
    counter: int
    history: Annotated[list, operator.add]


def node_a(state: State) -> dict:
    return {"counter": state["counter"] + 1, "history": ["a"]}


def node_b(state: State) -> dict:
    return {"counter": state["counter"] + 1, "history": ["b"]}


def node_c(state: State) -> dict:
    return {"counter": state["counter"] + 1, "history": ["c"]}


from langgraph.graph import StateGraph, END

builder = StateGraph(State)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)
builder.add_node("node_c", node_c)

builder.set_entry_point("node_a")

from typing import Literal


def route_from_a(state: State) -> Literal["node_b", "node_c", "__end__"]:
    if state["counter"] >= 5:
        return END
    if state["counter"] % 2 == 0:
        return "node_b"
    return "node_c"


def route_from_b(state: State) -> Literal["node_a", "__end__"]:
    if state["counter"] >= 5:
        return END
    return "node_a"


def route_from_c(state: State) -> Literal["node_a", "__end__"]:
    if state["counter"] >= 5:
        return END
    return "node_a"


builder.add_conditional_edges("node_a", route_from_a)
builder.add_conditional_edges("node_b", route_from_b)
builder.add_conditional_edges("node_c", route_from_c)

graph = builder.compile()
result = graph.invoke({"counter": 0, "history": []})
print(f"counter: {result['counter']}")
print(f"history: {result['history']}")
