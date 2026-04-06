import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.types import Command


class State(TypedDict):
    filename: str
    content: str
    result: str
    error: str
    retries: int


def write_file(state: State) -> Command:
    try:
        with open(state["filename"], "w") as f:
            f.write(state["content"])
        return Command(
            update={"result": f'File {state["filename"]} written successfully.'},
            goto="read_file",
        )
    except Exception as e:
        return Command(update={"error": str(e)}, goto="read_file")


def read_file(state: State) -> Command:
    try:
        with open(state["filename"], "r") as f:
            content = f.read()
            return Command(
                update={
                    "result": f'File {state["filename"]} read successfully',
                    "content": content,
                },
                goto=END,
            )
    except Exception as e:
        return Command(update={"error": str(e)}, goto="error_handler")


def error_handler(state: State) -> Command:
    if state["retries"] < 3:
        return Command(update={"retries": state["retries"] + 1}, goto="write_file")
    else:
        return Command(update={"result": "Failed after 3 retries"}, goto=END)


builder = StateGraph(State)
builder.add_node("write_file", write_file)
builder.add_node("read_file", read_file)
builder.add_node("error_handler", error_handler)
builder.set_entry_point("write_file")

graph = builder.compile()
result = graph.invoke(
    {
        "filename": "/nonexistent/path/test.txt",
        "content": "Hello LangGraph!",
        "result": "",
        "error": "",
        "retries": 0,
    }
)

print(f"result: {result['result']}")
print(f"content: {result['content']}")
