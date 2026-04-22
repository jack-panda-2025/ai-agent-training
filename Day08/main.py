from graph import get_graph


def run(url: str, thread_id: str = "day8-test-1"):
    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "url": url,
        "article_text": None,
        "summary": None,
        "translation": None,
        "messages": [],
        "next": "",
    }

    print(f"\n{'='*50}")
    print(f"Processing: {url}")
    print(f"{'='*50}\n")

    result = graph.invoke(initial_state, config=config)

    print("\n--- SUMMARY ---")
    print(result["summary"])
    print("\n--- CHINESE TRANSLATION ---")
    print(result["translation"])

    return result


if __name__ == "__main__":
    # Use any real tech article URL
    run("https://blog.langchain.dev/langgraph-v0-2/")
