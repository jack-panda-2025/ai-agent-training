from mcp.server.fastmcp import FastMCP
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(
    name="week2-mcp-server",
    instructions="A server with three tools: RAG knowledge base search, local file writing and GitHub issues fetching.",
)

# Initialize Chroma
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)


@mcp.tool(
    description="Search the knowledge base for relevant information. Use this when you need to answer questions about stored documents"
)
def query_rag(query: str) -> str:
    """
    query: the search question in natural language
    """
    docs = vectorstore.similarity_search(query, k=3)
    if not docs:
        return "No relevant documents found."

    results = []
    for i, doc in enumerate(docs):
        results.append(f"[{i+1}] {doc.page_content[:500]}")

    return "\n\n".join(results)


import os


@mcp.tool(
    description="Write text content to a local file. Use this to save results,reports, or any text output to disk."
)
def write_file(filename: str, content: str) -> str:
    """
    filename: the file path to write to (e.g. 'output/report.md)
    content: the text content to write
    """
    try:
        # create parent directories if they don't exist
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {filename}"
    except Exception as e:
        return f"ERROR: Could not write file - {str(e)}"


@mcp.tool(
    description="Fetch open issues from a public GitHub repository. Use this to get current issues,bugs, or feature requests from a repo."
)
def github_issues(repo: str, limit: int = 5) -> str:
    """
    repo: GitHub repository in 'owner/name' format (e.g. 'langchain-ai/langgraph')
    limit: number of issues to return, max 10
    """
    # Cap limit - protect against accidentally fetching hundreds of issues
    limit = min(limit, 10)

    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Add token if available — raises rate limit from 60 to 5000 requests/hour
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = httpx.get(
            url,
            headers=headers,
            params={"state": "open", "per_page": limit},
            timeout=10.0,
        )
        # Handle rate limiting explicitly
        if response.status_code == 403:
            return "ERROR: GitHub rate limit exceeded. Set GITHUB_TOKEN env var to increase limit."

        if response.status_code == 404:
            return f"ERROR: Repository '{repo}' not found. Check owner/name format."

        response.raise_for_status()
        issues = response.json()
        if not issues:
            return f"No open issues found in {repo}"

        results = []
        for issue in issues:
            results.append(
                f"#{issue['number']} {issue['title']}\n" f"  URL: {issue['html_url']}"
            )

        return f"Open issues in {repo}:\n\n" + "\n\n".join(results)
    except httpx.TimeoutException:
        return f"ERROR: Request timed out fetching issues form {repo}"
    except Exception as e:
        return f"ERROR:{str(e)}"
