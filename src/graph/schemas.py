from typing import Literal
from pydantic import BaseModel, Field

class RouterDecision(BaseModel):
    reasoning: str = Field(description="Explain why the routing decision was made")
    next_node: Literal["scraper_node", "rag_node"] = Field(
        description="The next node to route to: 'scraper_node' for Voz URLs or queries needing live scraped context, 'rag_node' for general knowledge queries"
    )
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
