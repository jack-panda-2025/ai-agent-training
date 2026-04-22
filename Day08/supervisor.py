from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import Literal
from state import AgentState
from dotenv import load_dotenv

load_dotenv()

WORKERS = ["fetcher", "summarizer", "translator"]


class RouteDecision(BaseModel):
    next: Literal["fetcher", "summarizer", "translator", "FINISH"]
    reasoning: str


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(RouteDecision)

SYSTEM_PROMPT = """You are a supervisor managing a team of workers to process a tech article.

Workers available:
- fetcher: Downloads the article from a URL. Must run first if article_text is missing.
- summarizer: Summarizes the article. Needs article_text. Run after fetcher.
- translator: Translates the summary to Chinese. Needs summary. Run after summarizer.

Rules:
1. Each worker runs exactly once.
2. Order must be: fetcher → summarizer → translator → FINISH
3. Check the current state to know what has already been done.
4. Output FINISH when all three workers have completed.

Current state will be described in the user message.
"""


def supervisor_node(state: AgentState) -> dict:
    """
    The supervisor reads current state and decides who runs next.

    Critical design insight: the supervisor doesn't DO any work.
    It only ROUTES. This separation of concerns is what makes the
    pattern maintainable — add a new worker without touching routing logic.
    """
    # Build a status description so the LLM knows what's done
    status = f"""
    URL provided: {state.get('url', 'None')}
    Article fetched: {'YES' if state.get('article_text') else 'NO'}
    Summary done: {'YES' if state.get('summary') else 'NO'}
    Translation done: {'YES' if state.get('translation') else 'NO'}
    """

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Current state:\n{status}\n\nWho should run next?"),
    ]

    decision = structured_llm.invoke(messages)
    print(f"[supervisor] → {decision.next} | reason: {decision.reasoning}")

    # Write the routing decision into state
    # The conditional edge in graph.py reads state["next"] to route
    return {"next": decision.next}


def route_after_supervisor(state: AgentState) -> str:
    """
    This is the conditional edge function — pure routing, no LLM.
    LangGraph calls this after supervisor_node runs and uses the
    return value to pick the next node.

    Design decision: keep this function dumb. All intelligence is in
    supervisor_node. This is just a state reader.
    """
    return state["next"]
