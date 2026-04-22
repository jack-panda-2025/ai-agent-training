# agents/code_fetcher.py
from state import RepoState
import subprocess
import shutil
import os


def code_fetcher_node(state: RepoState) -> dict:
    url = state["repo_url"]
    repo_name = url.split("/")[-1]
    local_path = f"/tmp/{repo_name}"

    print(f"[Code Fetcher] is clone {state['repo_url']}")

    if os.path.exists(local_path):
        shutil.rmtree(local_path)

    subprocess.run(["git", "clone", url, local_path], check=True)
    return {"local_repo_path": local_path}
