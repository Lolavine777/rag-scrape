from typing import TypedDict

class AgentState(TypedDict):
    question: str
    loop_count: int
