import httpx
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from state import AgentState
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# --- Fetcher ---
def fetcher_node(state: AgentState) -> dict:
    """
    Real HTTP fetch. No mock. Strips HTML tags, returns clean text.
    Design decision: we do this deterministically (no LLM needed to fetch a URL).
    LLMs are expensive — only use them where judgment is required.
    """
    print("[fetcher] Fetching", state["url"])
    try:
        response = httpx.get(state["url"], timeout=10, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        article_text = text[:8000]
    except Exception as e:
        article_text = f"Error: Could not fetch article - {str(e)}"

    return {"article_text": article_text}


# --- Summarizer ---
def summarizer_node(state: AgentState) -> dict:
    """
    Design decision: we check article_text exists before calling LLM.
    Defensive coding — never assume a previous node succeeded.
    """
    print("[summarizer] Summarizing article...")
    if not state.get("article_text") or state["article_text"].startswith("Error"):
        return {"summary": "Could not summarize - article fetch failed."}

    response = llm.invoke(
        f"Summarize this article in 3-5 bullet points. Be concise.\n\n{state['article_text']}"
    )
    return {"summary": response.content}


# --- Translator ---
def translator_node(state: AgentState) -> dict:
    """
    Translates the summary (not the full article — saves tokens).
    Design decision: translate the summary, not raw article text.
    """
    print("[translator] Translating to Chinese...")
    if not state.get("summary"):
        return {"translation": "翻译失败：没有摘要可供翻译"}

    response = llm.invoke(
        f"Translate the following to Simplified Chinese:\n\n{state['summary']}"
    )
    return {"translation": response.content}
