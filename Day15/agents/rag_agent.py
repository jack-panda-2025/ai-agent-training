from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

from state import RepoState
import os
import ast

QUESTIONS = [
    "Where is authentication handled?",
    "What are the main entry points?",
    "What external dependencies are used?",
]


def extract_functions(file_path: str) -> list[dict]:
    with open(file_path, "r") as f:
        source = f.read()

    tree = ast.parse(source)
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(
                {
                    "name": node.name,
                    "code": ast.get_source_segment(source, node),
                    "file": file_path,
                }
            )
    return functions


def rag_agent_node(state: RepoState) -> dict:
    chunks = []
    # 第一步：遍历所有 .py 文件，提取函数
    for root, dirs, files in os.walk(state["local_repo_path"]):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                chunks.extend(extract_functions(file_path))
    # 第二步：embed 进 Chroma
    docs = [
        Document(
            page_content=chunk["code"],
            metadata={"file": chunk["file"], "function": chunk["name"]},
        )
        for chunk in chunks
    ]
    vectorstore = Chroma.from_documents(
        documents=docs, embedding=OpenAIEmbeddings(), persist_directory="/tmp/chroma_db"
    )
    # 第三步：对每个 QUESTIONS 做检索 + LLM 回答
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model="gpt-4o-mini")
    results = {}
    for question in QUESTIONS:
        relevant_chunks = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in relevant_chunks])
        response = llm.invoke(
            f"""
根据以下代码回答问题：
{context}

问题：{question}
"""
        )
        results[question] = response.content

    # 返回 {"rag_result": {...}}
    return {"rag_result": results}
