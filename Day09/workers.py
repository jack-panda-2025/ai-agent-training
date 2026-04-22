import httpx
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from state import AgentState
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def fetcher_node(state: AgentState) -> Command:
    print("[fetcher] Fetching:", state["url"])
    try:
        response = httpx.get(state["url"], timeout=10, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        article_text = soup.get_text(separator="\n", strip=True)[:8000]
    except Exception as e:
        article_text = f"ERROR: {str(e)}"

    return Command(update={"article_text": article_text}, goto="summarizer")


# --- Summarizer ---
def summarizer_node(state: AgentState) -> Command:
    """
    Design decision: we check article_text exists before calling LLM.
    Defensive coding — never assume a previous node succeeded.
    """
    print("[summarizer] Summarizing article...")
    if not state.get("article_text") or state["article_text"].startswith("ERROR"):
        return Command(
            update={"summary": "Could not summarize - article fetch failed."},
            goto="__end__",
        )

    response = llm.invoke(
        f"Summarize this article in 3-5 bullet points. Be concise.\n\n{state['article_text']}"
    )
    return Command(update={"summary": response.content}, goto="translator")


# --- Translator ---
def translator_node(state: AgentState) -> Command:
    """
    Translates the summary (not the full article — saves tokens).
    Design decision: translate the summary, not raw article text.
    """
    print("[translator] Translating to Chinese...")
    if not state.get("summary"):
        return Command(
            update={"translation": "翻译失败：没有摘要可供翻译"}, goto="__end__"
        )

    response = llm.invoke(
        f"Translate the following to Simplified Chinese:\n\n{state['summary']}"
    )
    return Command(update={"translation": response.content}, goto="__end__")
