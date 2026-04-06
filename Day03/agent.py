import os
import requests
import subprocess
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]


class State(TypedDict):
    task: str
    filename: str
    content: str
    repo: str
    code: str
    output: str
    error: str
    retries: int
    issues: list  # add this


def router(state: State) -> Command:
    if state["task"] == "file":
        return Command(goto="write_file")
    elif state["task"] == "github":
        return Command(goto="fetch_issues")
    elif state["task"] == "code":
        return Command(goto="execute_code")
    else:
        return Command(update={"error": f"Unknown task: {state['task']}"}, goto=END)


def execute_code(state: State) -> Command:
    try:
        result = subprocess.run(
            ["python", "-c", state["code"]],
            capture_output=True,
            text=True,
            timeout=5,  # kill if runs more than 5 seconds
        )

        if result.returncode != 0:
            raise Exception(result.stderr)

        return Command(update={"output": result.stdout.strip()}, goto=END)
    except subprocess.TimeoutExpired:
        return Command(
            update={"error": "Code execution timed out after 5 seconds"},
            goto="error_handler",
        )
    except Exception as e:
        return Command(update={"error": str(e)}, goto="error_handler")


def write_file(state: State) -> Command:
    try:
        with open(state["filename"], "w") as f:
            f.write(state["content"])
        return Command(
            update={"result": f'File {state["filename"]} written successfully.'},
            goto="read_file",
        )
    except Exception as e:
        return Command(update={"error": str(e)}, goto="error_handler")  # not read_file


def read_file(state: State) -> Command:
    try:
        with open(state["filename"], "r") as f:
            content = f.read()
            return Command(
                update={
                    "result": f'File {state["filename"]} read successfully',
                    "content": content,
                },
                goto=END,
            )
    except Exception as e:
        return Command(update={"error": str(e)}, goto="error_handler")


def error_handler(state: State) -> Command:
    if state["retries"] < 3:
        return Command(update={"retries": state["retries"] + 1}, goto="router")
    else:
        return Command(update={"output": "Failed after 3 retries"}, goto=END)


def fetch_issues(state: State) -> Command:
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(
            f"https://api.github.com/repos/{state['repo']}/issues",
            headers=headers,
            timeout=10,
        )
        if response.status_code == 403:
            raise Exception("Rate limit exceeded")

        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}")

        issues = response.json()

        return Command(
            update={
                "issues": [i["title"] for i in issues[:5]],
                "result": f"Found {len(issues)} issues",
            },
            goto=END,
        )
    except Exception as e:
        return Command(update={"error": str(e)}, goto="error_handler")


builder = StateGraph(State)
builder.add_node("router", router)
builder.add_node("write_file", write_file)
builder.add_node("read_file", read_file)
builder.add_node("fetch_issues", fetch_issues)
builder.add_node("execute_code", execute_code)
builder.add_node("error_handler", error_handler)
builder.set_entry_point("router")

graph = builder.compile()

# test 1: file tool
result = graph.invoke(
    {
        "task": "file",
        "current_node": "",
        "filename": "test.txt",
        "content": "Hello from agent!",
        "repo": "",
        "code": "",
        "output": "",
        "error": "",
        "retries": 0,
    }
)
print(f"File result: {result['content']}")  # file tool sets content

# test 2: github tool
result = graph.invoke(
    {
        "task": "github",
        "current_node": "",
        "filename": "",
        "content": "",
        "repo": "langchain-ai/langgraph",
        "code": "",
        "output": "",
        "error": "",
        "retries": 0,
    }
)
print(f"GitHub result: {result['issues']}")  # github tool sets issues

# test 3: code tool
result = graph.invoke(
    {
        "task": "code",
        "current_node": "",
        "filename": "",
        "content": "",
        "repo": "",
        "code": "print(2 ** 10)",
        "output": "",
        "error": "",
        "retries": 0,
    }
)
print(f"Code result: {result['output']}")
