import os
from dotenv import load_dotenv

load_dotenv()

from typing import TypedDict
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import interrupt
from psycopg import Connection

# --- Vector store ---
docs = [
    "Python is a high-level programming language known for simplicity.",
    "Python supports object-oriented, functional, and procedural programming.",
    "Python is widely used in data science, machine learning, and web development.",
    "JavaScript is the primary language for web frontend development.",
    "JavaScript runs in the browser and enables interactive web pages.",
]

embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_texts(docs, embedding=embeddings)
llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)


# --- State ---
class RAGState(TypedDict):
    query: str
    documents: list
    confidence: float
    human_decision: str
    answer: str


# --- Nodes ---
def retrieve_node(state: RAGState):
    results = vectorstore.similarity_search_with_relevance_scores(state["query"], k=2)
    if not results:
        return {"documents": [], "confidence": 0.0}
    docs = [doc.page_content for doc, _ in results]
    confidence = results[0][1]
    return {"documents": docs, "confidence": confidence}


def route_after_retrieve(state: RAGState):
    if not state["documents"]:
        return "fallback"
    if state["confidence"] < 0.7:
        return "human_review"
    return "generate"


def human_review_node(state: RAGState):
    decision = interrupt(
        {
            "question": "Retrieval confidence is low. Approve or reject?",
            "confidence": state["confidence"],
            "documents": state["documents"],
            "query": state["query"],
        }
    )
    return {"human_decision": decision}


def generate_node(state: RAGState):
    decision = state.get("human_decision", "auto")
    if decision == "reject":
        return {"answer": "Rejected by human reviewer."}
    context = "\n".join(state["documents"])
    response = llm.invoke(
        f"Answer based on context:\n{context}\n\nQuestion: {state['query']}"
    )
    return {"answer": response.content}


def fallback_node(state: RAGState):
    return {"answer": "No relevant documents found."}


# --- Graph ---
builder = StateGraph(RAGState)
builder.add_node("retrieve", retrieve_node)
builder.add_node("human_review", human_review_node)
builder.add_node("generate", generate_node)
builder.add_node("fallback", fallback_node)

builder.add_edge(START, "retrieve")
builder.add_conditional_edges(
    "retrieve",
    route_after_retrieve,
    {"human_review": "human_review", "generate": "generate", "fallback": "fallback"},
)
builder.add_edge("human_review", "generate")
builder.add_edge("generate", END)
builder.add_edge("fallback", END)

# --- Checkpointer ---
DB_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/checkpoints")
conn = Connection.connect(DB_URI, autocommit=True)
checkpointer = PostgresSaver(conn)
checkpointer.setup()
graph = builder.compile(checkpointer=checkpointer)
