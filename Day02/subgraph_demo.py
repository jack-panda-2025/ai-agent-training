import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.types import Command


class State(TypedDict):
    counter: int
    history: Annotated[list, operator.add]


def sub_node_1(state: State) -> Command:
    return Command(update={"history": ["sub1"]}, goto="sub_node_2")


def sub_node_2(state: State) -> Command:
    return Command(update={"history": ["sub2"]}, goto="sub_exit")


def sub_exit(state: State) -> Command:
    # only this node jumps to parent, no logic here
    return Command(
        update=({"history": state["history"]}), goto="node_b", graph=Command.PARENT
    )


sub_builder = StateGraph(State)
sub_builder.add_node("sub_node_1", sub_node_1)
sub_builder.add_node("sub_node_2", sub_node_2)
sub_builder.add_node("sub_exit", sub_exit)
sub_builder.set_entry_point("sub_node_1")

subgraph = sub_builder.compile()


def node_a(state: State) -> Command:
    return Command(update={"history": ["a"]}, goto="subgraph")


def node_b(state: State) -> dict:
    return {"history": ["b"]}


builder = StateGraph(State)
builder.add_node("node_a", node_a)
builder.add_node("subgraph", subgraph)
builder.add_node("node_b", node_b)
builder.set_entry_point("node_a")

graph = builder.compile()

result = graph.invoke({"counter": 0, "history": []})
print(f"history: {result['history']}")
