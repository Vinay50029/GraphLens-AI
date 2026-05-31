import operator
import requests
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import SystemMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from api.utils.llm_factory import get_llm


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    active_document: str


@tool
def scrape_website(url: str) -> str:
    """
    Scrapes and returns text content from a given URL.
    Use this when the user provides a specific link to read.
    """
    try:
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=15)
        response.raise_for_status()
        return response.text[:10000]  # Jina Reader returns clean markdown, so we can handle up to 10k chars
    except Exception as e:
        return f"Failed to retrieve website content: {str(e)}"


def researcher_node(state: AgentState):
    """Web researcher agent — searches the internet and scrapes URLs to answer questions."""
    messages = state["messages"]
    question = messages[-1].content

    search = DuckDuckGoSearchRun()

    history_msgs = messages[-5:-1] if len(messages) > 1 else []
    conversation_history = ""
    if history_msgs:
        history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in history_msgs])
        conversation_history = f"Recent Conversation:\n{history_str}\n"

    llm = get_llm(temperature=0.0)
    agent_executor = create_react_agent(llm, tools=[search, scrape_website])

    system_prompt = SystemMessage(content=f"""You are a helpful AI research assistant.
You have tools to search the web (DuckDuckGo) and scrape specific URLs.
If the user provides a specific link, ALWAYS use the scrape_website tool to read it first before answering.
If search results are missing, failed, or irrelevant, fallback to your own general knowledge.

{conversation_history}""")

    inputs = {"messages": [system_prompt, messages[-1]]}
    result = agent_executor.invoke(inputs)
    return {"messages": [result["messages"][-1]]}
