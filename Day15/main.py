from langgraph.types import interrupt
from graph import build_graph
from langgraph.types import Command


def main():
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-1"}}

    print("=== 开始分析 ===")

    # 第一次运行，可能在 HITL 处暂停
    result = graph.invoke(
        {"repo_url": "https://github.com/langchain-ai/langchain-extract"}, config=config
    )

    # 检查是否被 interrupt 暂停
    if "__interrupt__" in result:
        print("\n⚠️  HITL 触发：安全分析置信度低")
        print("发现的问题需要人工审核")
        print(graph.get_state(config).values.get("security_result"))

        input("\n按回车键确认审核完成，继续生成报告...")

        # 恢复执行
    result = graph.invoke(Command(resume="approved"), config=config)

    print("\n=== 最终报告 ===")
    print(result["report"])


if __name__ == "__main__":
    main()
