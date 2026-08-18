import operator
from typing import Annotated, Literal, Optional, TypedDict
from langgraph.graph import StateGraph, START, END

from api.agents.supervisor import supervisor_node
from api.agents.document_agent import document_node
from api.agents.researcher import researcher_node
from api.agents.file_agent import file_node
from api.agents.email_agent import email_node


class GraphState(TypedDict):
    messages: Annotated[list, operator.add]
    next_agent: str
    active_documents: list[str]
    user_id: int
    user_email: Optional[str]
    user_name: Optional[str]


def router(state: GraphState) -> Literal["document_agent", "researcher_agent", "file_agent", "email_agent"]:
    """Routing function that reads the supervisor's decision."""
    return state["next_agent"]


def create_workflow():
    """Builds and compiles the LangGraph workflow."""
    workflow = StateGraph(GraphState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("document_agent", document_node)
    workflow.add_node("researcher_agent", researcher_node)
    workflow.add_node("file_agent", file_node)
    workflow.add_node("email_agent", email_node)

    workflow.add_edge(START, "supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        router,
        {
            "document_agent": "document_agent",
            "researcher_agent": "researcher_agent",
            "file_agent": "file_agent",
            "email_agent": "email_agent",
        }
    )

    workflow.add_edge("document_agent", END)
    workflow.add_edge("researcher_agent", END)
    workflow.add_edge("file_agent", END)
    workflow.add_edge("email_agent", END)

    return workflow.compile()


