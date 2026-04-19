from typing import Annotated, Literal
import operator
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from api.utils.llm_factory import get_llm


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    active_document: str


class RouteSchema(BaseModel):
    next_node: Literal["document_agent", "researcher_agent"] = Field(
        description="The next agent to route the query to."
    )


def _looks_like_web_query(question: str) -> bool:
    q = question.lower()
    web_hints = [
        "latest",
        "today",
        "news",
        "current",
        "recent",
        "internet",
        "online",
        "web",
        "search",
        "google",
        "duckduckgo",
        "http://",
        "https://",
        "www.",
    ]
    return any(token in q for token in web_hints)


def supervisor_node(state: AgentState):
    """Analyzes the user request and routes it to the appropriate worker agent."""
    messages = state["messages"]

    question = messages[-1].content
    active_document = (state.get("active_document") or "").strip()

    # Deterministic preference: when a document is active, keep routing to document_agent
    # unless the user clearly asks for web/current-events information.
    if active_document and not _looks_like_web_query(question):
        return {"next_agent": "document_agent"}

    llm = get_llm(temperature=0.0)
    router_llm = llm.with_structured_output(RouteSchema)

    history_msgs = messages[-5:-1] if len(messages) > 1 else []
    conversation_history = ""
    if history_msgs:
        history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in history_msgs])
        conversation_history = f"Recent Conversation:\n{history_str}\n"

    prompt = f"""You are the supervisor of a research assistant system. Your job is to route the user's question to the correct specialist.

    Available specialists:
    1. 'document_agent': Use this IF the user is asking about a specific PDF they uploaded, a document provided to you, or asking to summarize "my document", "the given context", or "the text".
    2. 'researcher_agent': Use this IF the question requires up-to-date information, facts from the internet, current events, or general knowledge not contained in a specific local document.

    {conversation_history}
    User Query: {question}
    """

    decision = router_llm.invoke(prompt)
    return {"next_agent": decision.next_node}
