from typing import Literal, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    url: str
    article_text: Optional[str]
    summary: Optional[str]
    translation: Optional[str]
    messages: list
    next: str
