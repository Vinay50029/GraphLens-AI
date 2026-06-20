from typing import Annotated, Literal
import operator
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from api.utils.llm_factory import get_llm


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    active_document: str
    user_id: int


class RouteSchema(BaseModel):
    next_node: Literal["document_agent", "researcher_agent", "file_agent"] = Field(
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


def _looks_like_file_query(question: str) -> bool:
    q = question.lower()
    
    # 1. Action verb + File extension (e.g. "create notes.txt")
    has_ext = any(ext in q for ext in [".txt", ".pdf"])
    file_actions = ["create", "write", "save", "delete", "remove", "read", "view", "update", "edit", "make", "list", "append", "add", "overwrite"]
    if has_ext and any(action in q for action in file_actions):
        return True
        
    # 2. General file/folder phrase indicators
    file_hints = [
        "create a file",
        "create file",
        "write to file",
        "save file",
        "save to file",
        "delete file",
        "remove file",
        "read file",
        "view file",
        "update file",
        "edit file",
        "list file",
        "list my file",
        "my files",
        "what files",
        "files in my workspace",
        "show my files",
        "list all files"
    ]
    if any(hint in q for hint in file_hints):
        return True
        
    # 3. Action verb + target pronouns/words (e.g. "delete the selected file", "read it", "update this")
    targets = ["file", "it", "this", "content", "data"]
    if any(t in q for t in targets) and any(action in q for action in file_actions):
        return True
        
    # 4. Standalone distinctive file-management action verbs
    distinct_verbs = ["append", "overwrite", "create file", "delete file", "read file", "write file"]
    if any(verb in q for verb in distinct_verbs):
        return True
        
    return False


def supervisor_node(state: AgentState):
    """Analyzes the user request and routes it to the appropriate worker agent."""
    messages = state["messages"]

    question = messages[-1].content
    active_document = (state.get("active_document") or "").strip()

    # If it is a file operation, always route to file_agent
    if _looks_like_file_query(question):
        return {"next_agent": "file_agent"}

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
    3. 'file_agent': Use this IF the user asks to manage their files, such as creating, reading, listing, updating, editing, or deleting files. (e.g. 'list my files', 'create a file named notes.txt', 'what is in report.txt', 'delete file.txt').

    {conversation_history}
    User Query: {question}
    """

    decision = router_llm.invoke(prompt)
    return {"next_agent": decision.next_node}

