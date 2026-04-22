from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import RepoState, HITLStatus
from agents.code_fetcher import code_fetcher_node
from agents.rag_agent import rag_agent_node
from agents.security_analyzer import security_analyzer_node
from agents.report_agent import report_agent_node
from langgraph.types import interrupt


def hitl_node(state: RepoState):
    if state["confidence"] < 0.7:
        interrupt("低置信度，请人工审核安全分析结果")
    return {"hitl_status": HITLStatus.COMPLETED}


def build_graph():
    builder = StateGraph(RepoState)

    # 添加节点
    builder.add_node("code_fetcher", code_fetcher_node)
    builder.add_node("rag_agent", rag_agent_node)  # rag_agent
    builder.add_node("security_analyzer", security_analyzer_node)  # security_analyzer
    builder.add_node("hitl", hitl_node)  # hitl
    builder.add_node("report_agent", report_agent_node)  # report_agent

    # 连边
    builder.add_edge(START, "code_fetcher")
    builder.add_edge("code_fetcher", "rag_agent")  # 并行第一条
    builder.add_edge("code_fetcher", "security_analyzer")  # 并行第二条
    builder.add_edge("security_analyzer", "hitl")
    builder.add_edge(["hitl", "rag_agent"], "report_agent")  # rag 汇聚
    builder.add_edge("report_agent", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)
