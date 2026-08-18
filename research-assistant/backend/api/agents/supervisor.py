from typing import Annotated, Literal
import operator
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from api.utils.llm_factory import get_llm


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    active_documents: list[str]
    user_id: int


class RouteSchema(BaseModel):
    next_node: Literal["document_agent", "researcher_agent", "file_agent", "email_agent"] = Field(
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


def _looks_like_email_query(question: str) -> bool:
    q = question.lower()
    email_hints = [
        "send email",
        "send mail",
        "send pdf to",
        "email this",
        "email file",
        "email document",
        "email report",
        "send to my friend",
        "mail to",
        "send an email",
        "email to",
        "forward file",
        "mail this",
    ]
    if any(hint in q for hint in email_hints):
        return True
    if "@" in q and any(w in q for w in ["send", "email", "mail", "attach", "forward"]):
        return True
    return False


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
    active_documents = state.get("active_documents") or []

    # Deterministic checks
    if _looks_like_email_query(question):
        return {"next_agent": "email_agent"}

    if _looks_like_file_query(question):
        return {"next_agent": "file_agent"}

    llm = get_llm(temperature=0.0)
    router_llm = llm.with_structured_output(RouteSchema)

    history_msgs = messages[-5:-1] if len(messages) > 1 else []
    conversation_history = ""
    if history_msgs:
        history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in history_msgs])
        conversation_history = f"Recent Conversation:\n{history_str}\n"

    active_docs_str = f"Active Documents: {', '.join(active_documents)}" if active_documents else "No active documents selected."

    prompt = f"""You are the supervisor of a research assistant system. Your job is to route the user's question to the correct specialist.

    Current Workspace State:
    {active_docs_str}

    Available specialists:
    1. 'document_agent': Use this IF the user is asking about the content of the active documents, specific PDFs they uploaded, or asking to analyze/summarize "the document", "the given context", or "the text".
    2. 'researcher_agent': Use this IF the question requires general knowledge (e.g. word definitions, math calculations, general logic), up-to-date information, facts from the internet, or current events.
    3. 'file_agent': Use this IF the user asks to manage their files, such as creating, reading, listing, updating, editing, or deleting files. (e.g. 'list my files', 'create a file named notes.txt', 'what is in report.txt', 'delete file.txt').
    4. 'email_agent': Use this IF the user asks to send an email, mail a document/file, or forward a PDF file to a recipient email address (e.g. 'send report.pdf to friend@gmail.com', 'email this document to user@example.com').

    {conversation_history}
    User Query: {question}
    """

    decision = router_llm.invoke(prompt)
    return {"next_agent": decision.next_node}


