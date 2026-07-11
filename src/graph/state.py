from typing import TypedDict, Optional

class AgentState(TypedDict):
    question: str
    loop_count: int
    url: Optional[str]
    retrieved_context: Optional[str]
    answer: Optional[str]
    route_decision: Optional[str]
