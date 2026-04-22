import streamlit as st
from graph import build_graph
from langgraph.types import Command

st.title("Code Repository Intelligence Platform")

url = st.text_input("输入 GitHub Repo URL", placeholder="https://github.com/user/repo")

if st.button("开始分析") and url:
    graph = build_graph()
    config = {"configurable": {"thread_id": url}}

    with st.status("正在分析...", expanded=True) as status:
        st.write("🔍 Code Fetcher: 正在 clone repo...")

        result = graph.invoke({"repo_url": url}, config=config)

        # 处理 HITL
        if "__interrupt__" in result:
            status.update(label="⚠️ 需要人工审核", state="error")
            st.warning("安全分析置信度低，请审核后点击继续")
            st.code(result.get("security_result", ""))

            if st.button("确认审核完成，继续生成报告"):
                result = graph.invoke(Command(resume="approved"), config=config)
        else:
            status.update(label="✅ 分析完成", state="complete")

    # 显示报告
    if "report" in result:
        st.markdown(result["report"])
