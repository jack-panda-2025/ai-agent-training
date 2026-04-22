from typing import TypedDict
from enum import Enum


class HITLStatus(Enum):
    NOT_TRIGGERED = 0
    WAITING = 1
    COMPLETED = 2


class RepoState(TypedDict):
    repo_url: str
    local_repo_path: str
    security_result: str
    confidence: float
    rag_result: dict[str, str]
    hitl_status: HITLStatus
    report: str
