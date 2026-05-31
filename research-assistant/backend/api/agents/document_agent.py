import operator
import re
from typing import Annotated
from typing_extensions import TypedDict

from api.utils.llm_factory import get_llm
from api.rag.retrieve import get_retriever, get_vectorstore


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    active_document: str
    user_id: int


def document_node(state: AgentState):
    """Answers questions based on retrieved documents from Pinecone."""
    messages = state["messages"]
    question = messages[-1].content
    user_id = state.get("user_id")

    active_document = (state.get("active_document") or "").strip() or None
    
    # 1. Detect if the user named an explicit file name in the question
    filename_match = re.search(r"([\w\-. ]+\.(?:pdf|docx|doc|txt))\b", question, flags=re.IGNORECASE)
    explicit_file_name = filename_match.group(1).strip() if filename_match else None
    
    scoped_file_name = explicit_file_name or active_document

    # 2. Get retriever based on active/explicit document, or globally if none is active
    retriever = get_retriever(user_id, scoped_file_name) if user_id else None
    
    docs = []
    if retriever:
        docs = retriever.invoke(question)

    # 3. Construct context text from retrieved document chunks
    if docs:
        context = "\n\n".join([doc.page_content for doc in docs])
    elif scoped_file_name:
        context = f"No chunks were found for '{scoped_file_name}'. Please make sure the document is ingested."
    else:
        context = "No documents have been loaded into the database yet. Please upload and ingest a document first."

    # 5. Format history and create final prompt for the LLM
    history_msgs = messages[-5:-1] if len(messages) > 1 else []
    conversation_history = ""
    if history_msgs:
        history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in history_msgs])
        conversation_history = f"Recent Conversation:\n{history_str}\n"

    prompt = f"""You are a helpful research assistant. Answer the user's question based strictly on the provided context.
If the context doesn't contain the answer, say that you don't know based on the provided documents.

Context:
{context}

{conversation_history}
Question: {question}
"""

    llm = get_llm(temperature=0.2)
    response = llm.invoke(prompt)
    return {"messages": [response]}
