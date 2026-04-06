import os
import requests
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from dotenv import load_dotenv

load_dotenv()


class State(TypedDict):
    repo: str
    issues: list
    result: str
    error: str
    retries: int


GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]


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
        return Command(update={"retries": state["retries"] + 1}, goto="fetch_issues")
    else:
        return Command(update={"result": "Failed after 3 retries"}, goto=END)


builder = StateGraph(State)
builder.add_node("fetch_issues", fetch_issues)
builder.add_node("error_handler", error_handler)
builder.set_entry_point("fetch_issues")

graph = builder.compile()

result = graph.invoke(
    {
        "repo": "langchain-ai/langgraph",
        "issues": [],
        "result": "",
        "error": "",
        "retries": 0,
    }
)

print(f"result:{result['result']}")
print(f"issues:{result['issues']}")
