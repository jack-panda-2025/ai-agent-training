import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.types import Command


class State(TypedDict):
    counter: int
    history: Annotated[list, operator.add]


def node_a(state: State) -> Command:
    next_node = "node_b" if state["counter"] + 1 < 4 else END
    return Command(
        update={"counter": state["counter"] + 1, "history": ["a"]}, goto=next_node
    )


def node_b(state: State) -> Command:
    next_node = "node_a" if state["counter"] + 1 < 4 else END
    return Command(
        update={"counter": state["counter"] + 1, "history": ["b"]}, goto=next_node
    )


builder = StateGraph(State)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)
builder.set_entry_point("node_a")

graph = builder.compile()
result = graph.invoke({"counter": 0, "history": []})
print(f"完成! counter={result['counter']}, history={result['history']}")
