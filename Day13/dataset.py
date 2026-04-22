# dataset.py
from langsmith import Client
from dotenv import load_dotenv

load_dotenv()

client = Client()

DATASET_NAME = "week2-rag-evaluation"

examples = [
    # Checkpoints (7 questions)
    {
        "question": "What is a LangGraph checkpoint?",
        "answer": "A checkpoint is a snapshot of the graph state at a specific point during execution, saved after every node execution.",
    },
    {
        "question": "What are the three features that checkpoints enable?",
        "answer": "Memory persistence across sessions, error recovery by resuming from last saved state, and time travel by rolling back to previous checkpoints.",
    },
    {
        "question": "What is the difference between MemorySaver and PostgresSaver?",
        "answer": "MemorySaver stores checkpoints in memory and loses them when process exits. PostgresSaver stores in PostgreSQL and persists across restarts.",
    },
    {
        "question": "Which checkpointer is recommended for production?",
        "answer": "PostgresSaver is recommended for production because it persists across restarts.",
    },
    {
        "question": "How do you pass a checkpointer to a LangGraph graph?",
        "answer": "Pass it to graph.compile() like this: graph = builder.compile(checkpointer=PostgresSaver(conn))",
    },
    {
        "question": "What is thread_id used for in LangGraph?",
        "answer": "thread_id identifies each run in the config, used to separate different conversation sessions.",
    },
    {
        "question": "When would you use MemorySaver over PostgresSaver?",
        "answer": "MemorySaver is good for development and testing because it is simpler to set up, but not for production.",
    },
    # StateGraph (7 questions)
    {
        "question": "What does a StateGraph node receive as input?",
        "answer": "Every node receives the full current state as input and returns a dict of updates.",
    },
    {
        "question": "What is the default reducer behavior in StateGraph?",
        "answer": "The default reducer overwrites the field with the new value.",
    },
    {
        "question": "How do you append to a state field instead of overwriting it?",
        "answer": "Use Annotated with operator.add to append instead of overwrite.",
    },
    {
        "question": "What are the three types of edges in StateGraph?",
        "answer": "Regular edges that always go from A to B, conditional edges that use a function to decide at runtime, and entry point that sets which node runs first.",
    },
    {
        "question": "What is the difference between StateGraph and MessageGraph?",
        "answer": "MessageGraph is a subclass where state is always a list of messages. StateGraph is more flexible and supports custom state fields.",
    },
    {
        "question": "When should you use StateGraph over MessageGraph?",
        "answer": "Use StateGraph when you need custom state fields beyond messages.",
    },
    {
        "question": "What schema does StateGraph require?",
        "answer": "A TypedDict that defines what data flows through the graph.",
    },
    # HITL (6 questions)
    {
        "question": "What does human-in-the-loop mean in LangGraph?",
        "answer": "Pausing graph execution to wait for human input or approval before continuing.",
    },
    {
        "question": "How does LangGraph implement human-in-the-loop?",
        "answer": "Using interrupt(). When called, the graph saves state as a checkpoint and pauses execution.",
    },
    {
        "question": "What is the difference between interrupt() and input() in LangGraph?",
        "answer": "interrupt() is async and process-safe — the process can exit while waiting. input() blocks the process.",
    },
    {
        "question": "What are three common use cases for HITL?",
        "answer": "Approval workflows, confidence threshold reviews when retrieval score is low, and sensitive operations requiring human confirmation.",
    },
    {
        "question": "How do you resume a graph after interrupt()?",
        "answer": "Invoke the graph with the same thread_id and pass the human's response as input.",
    },
    {
        "question": "Why is interrupt() better than input() for production?",
        "answer": "Because the graph does not need to stay running while waiting for human input — state is persisted and process can safely exit.",
    },
]


def create_dataset():
    # Check if dataset already exists
    datasets = list(
        client.list_datasets(dataset_name=DATASET_NAME)
    )  # 返回生成器，用list展开
    if datasets:
        print(f"Dataset '{DATASET_NAME}' already exists, deleting and recreating...")
        client.delete_dataset(dataset_id=datasets[0].id)
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="20 Q&A pairs for evaluating RAG system on LangGraph docs",
    )

    # Upload examples
    client.create_examples(
        inputs=[{"question": e["question"]} for e in examples],
        outputs=[{"answer": e["answer"]} for e in examples],
        dataset_id=dataset.id,
    )

    print(f"Created dataset '{DATASET_NAME}' with {len(examples)} examples")
    return dataset


if __name__ == "__main__":
    create_dataset()
