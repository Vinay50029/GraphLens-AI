import operator
from typing import Annotated, Literal, TypedDict
from langgraph.graph import StateGraph, START, END

from api.agents.supervisor import supervisor_node
from api.agents.document_agent import document_node
from api.agents.researcher import researcher_node


class GraphState(TypedDict):
    messages: Annotated[list, operator.add]
    next_agent: str
    active_document: str


def router(state: GraphState) -> Literal["document_agent", "researcher_agent"]:
    """Routing function that reads the supervisor's decision."""
    return state["next_agent"]


def create_workflow():
    """Builds and compiles the LangGraph workflow."""
    workflow = StateGraph(GraphState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("document_agent", document_node)
    workflow.add_node("researcher_agent", researcher_node)

    workflow.add_edge(START, "supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        router,
        {
            "document_agent": "document_agent",
            "researcher_agent": "researcher_agent",
        }
    )

    workflow.add_edge("document_agent", END)
    workflow.add_edge("researcher_agent", END)

    return workflow.compile()
