# agents/security_analyzer.py
from state import RepoState


def report_agent_node(state: RepoState) -> dict:
    print("[Report Agent] 正在生成报告")

    rag_section = "\n".join([f"**{q}**\n{a}" for q, a in state["rag_result"].items()])

    report = f"""
# 代码分析报告

## 安全分析
{state['security_result']}

## 代码理解
{rag_section}
    """
    return {"report": report}
