import operator
import time
from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver


class State(TypedDict):
    counter: int
    history: Annotated[list, operator.add]


def node_a(state: State) -> dict:
    print(f"node_a 运行中... counter={state['counter']}")
    time.sleep(5)
    return {"counter": state["counter"] + 1, "history": ["a"]}


def node_b(state: State) -> dict:
    print(f"node_b 运行中... counter={state['counter']}")
    time.sleep(5)
    return {"counter": state["counter"] + 1, "history": ["b"]}


def route(state: State) -> Literal["node_b", "__end__"]:
    if state["counter"] >= 4:
        return END
    return "node_b"


def route_b(state: State) -> Literal["node_a", "__end__"]:
    if state["counter"] >= 4:
        return END
    return "node_a"


checkpointer = SqliteSaver.from_conn_string("checkpoint.db")
builder = StateGraph(State)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)

builder.set_entry_point("node_a")
builder.add_conditional_edges("node_a", route)
builder.add_conditional_edges("node_b", route_b)

with SqliteSaver.from_conn_string("checkpoint.db") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "test-001"}}

    # 检查是否有已存在的 checkpoint
    existing = checkpointer.get(config)
    if existing:
        print("找到 checkpoint，从断点恢复...")
        result = graph.invoke(None, config=config)
    else:
        print("没有 checkpoint，从头开始...")
        result = graph.invoke({"counter": 0, "history": []}, config=config)

    print(f"完成! counter={result['counter']}, history={result['history']}")
