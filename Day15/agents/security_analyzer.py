import re
import ast
import os
from state import RepoState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# 三类检测 pattern
PATTERNS = {
    "hardcoded_secret": r'(?i)(password|secret|api_key|token)\s*=\s*["\'][^"\']{4,}["\']',
    "sql_injection": r'(?i)(execute|query)\s*\(\s*["\'].*%s.*["\']|f["\'].*SELECT.*\{',
}


def scan_file(file_path: str) -> list[dict]:
    findings = []
    with open(file_path, "r", errors="ignore") as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        for issue_type, pattern in PATTERNS.items():
            if re.search(pattern, line):
                findings.append(
                    {
                        "type": issue_type,
                        "file": file_path,
                        "line": i,
                        "code": line.strip(),
                    }
                )
    return findings


def security_analyzer_node(state: RepoState) -> dict:
    # 第一步：deterministic 扫描
    all_findings = []
    for root, dirs, files in os.walk(state["local_repo_path"]):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                all_findings.extend(scan_file(file_path))

    # 第二步：LLM 解释
    confidence = 0.9 if all_findings else 1.0

    if all_findings:
        llm = ChatOpenAI(model="gpt-4o-mini")
        findings_text = "\n".join(
            [
                f"- [{f['type']}] {f['file']}:{f['line']} → {f['code']}"
                for f in all_findings
            ]
        )
        response = llm.invoke(
            f"""
以下是代码安全扫描结果，请解释每个问题的危害和修复建议：
{findings_text}
"""
        )
        security_result = response.content
        confidence = 0.6 if len(all_findings) > 5 else 0.9
    else:
        security_result = "未发现安全问题"

    return {"security_result": security_result, "confidence": confidence}
