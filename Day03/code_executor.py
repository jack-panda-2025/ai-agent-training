import subprocess
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.types import Command


class State(TypedDict):
    code: str  # the Python code to execute
    output: str  # stdout result
    error: str  # error message if any
    retries: int


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


def error_handler(state: State) -> Command:
    if state["retries"] < 3:
        return Command(update={"retries": state["retries"] + 1}, goto="execute_code")
    else:
        return Command(update={"output": "failed after 3 retries"}, goto=END)


builder = StateGraph(State)
builder.add_node("execute_code", execute_code)
builder.add_node("error_handler", error_handler)
builder.set_entry_point("execute_code")


graph = builder.compile()

# test 1: normal code
result = graph.invoke({"code": "print(1 + 1)", "output": "", "error": "", "retries": 0})
print(f"output: {result['output']}")

# test 2: timeout
result = graph.invoke(
    {"code": "while True: pass", "output": "", "error": "", "retries": 0}
)
print(f"output: {result['output']}")
