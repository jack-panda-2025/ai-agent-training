import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.types import Command


class State(TypedDict):
    query: str
    documents: list
    answer: str


def retrieve(state: State) -> Command:
    query = state["query"]

    if "python" in query.lower():
        docs = ["Python is a programming language.", "Python supports OOP"]
    else:
        docs = []

    if docs:
        return Command(update={"documents": docs}, goto="generate_answer")
    else:
        return Command(update={"documents": []}, goto="fallback")


def generate_answer(state: State) -> dict:
    docs = state["documents"]
    answer = f"Based on the retrieved documents: {', '.join(docs)}"
    return {"answer": answer}


def fallback(state: State) -> dict:
    return {"answer": "No relevant documents found."}


builder = StateGraph(State)
builder.add_node("retrieve", retrieve)
builder.add_node("generate_answer", generate_answer)
builder.add_node("fallback", fallback)
builder.set_entry_point("retrieve")

graph = builder.compile()
# test 1
result = graph.invoke({"query": "What is Python?", "documents": [], "answer": ""})
print(f"Q: tell me about Python?")
print(f"A: {result['answer']}")
# test 2
result = graph.invoke({"query": "What is Java?", "documents": [], "answer": ""})
print(f"Q: tell me about Java?")
print(f"A: {result['answer']}")
