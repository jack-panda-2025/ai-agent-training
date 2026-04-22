from langsmith import Client
from langsmith.evaluation import evaluate
from langchain_openai import ChatOpenAI
from rag import get_rag_chain
import time
from dotenv import load_dotenv

load_dotenv()

client = Client()
DATASET_NAME = "week2-rag-evaluation"

# Initialize RAG chain once — reused for all 20 questions
rag_chain = get_rag_chain()


def predict(inputs: dict) -> dict:
    """
    LangSmith calls this function for every example in the dataset.
    inputs = {"question": "What is a checkpoint?"}
    Must return a dict — evaluators read from it.
    """
    start = time.time()
    result = rag_chain(inputs["question"])
    result["latency"] = time.time() - start
    return result


# Evaluator 1 — correctness (LLM-as-judge)
# Compares RAG answer against reference answer
llm_judge = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def correctness_evaluator(run, example) -> dict:
    """
    LLM-as-judge: compare RAG answer against reference answer.
    """
    question = example.inputs["question"]
    reference = example.outputs["answer"]
    prediction = run.outputs["answer"]

    prompt = f"""You are grading a RAG system answer.

Question: {question}
Reference answer: {reference}
RAG answer: {prediction}

Score the RAG answer from 1-10 for correctness.
Reply with ONLY a number between 1 and 10, nothing else."""

    response = llm_judge.invoke(prompt)

    try:
        score = float(response.content.strip()) / 10
    except:
        score = 0.5

    return {"key": "correctness", "score": score}


# Evaluator 2 — retrieval recall
# Did we retrieve documents that contain the answer?
def retrieval_recall(run, example) -> dict:
    """
    Checks if the reference answer keywords appear in retrieved context.
    Simple but effective proxy for retrieval quality.
    """
    context = run.outputs.get("context", "")
    reference = example.outputs["answer"].lower()

    # Extract key words from reference answer (words > 4 chars)
    key_words = [w for w in reference.split() if len(w) > 4]

    if not key_words:
        return {"key": "retrieval_recall", "score": 0.0}

    # What fraction of key words appear in retrieved context?
    found = sum(1 for w in key_words if w in context.lower())
    score = found / len(key_words)

    return {"key": "retrieval_recall", "score": score}


# Evaluator 3 — latency
def latency_evaluator(run, example) -> dict:
    latency = run.outputs.get("latency", 0)
    return {"key": "latency_seconds", "score": latency}


def run_evaluation(experiment_name: str = "baseline-k2"):
    print(f"\nRunning evaluation: {experiment_name}")
    print(f"Dataset: {DATASET_NAME}")
    print(f"{'='*50}\n")

    results = evaluate(
        predict,
        data=DATASET_NAME,
        evaluators=[
            correctness_evaluator,
            retrieval_recall,
            latency_evaluator,
        ],
        experiment_prefix=experiment_name,
        metadata={"k": 4, "chunk_size": 500},  # track parameters
    )

    # Print summary
    print("\n--- RESULTS ---")
    df = results.to_pandas()

    for metric in ["correctness", "retrieval_recall", "latency_seconds"]:
        cols = [c for c in df.columns if metric in c.lower()]
        if cols:
            avg = df[cols[0]].mean()
            print(f"{metric}: {avg:.3f}")

    return results


if __name__ == "__main__":
    run_evaluation("k4-experiment")
