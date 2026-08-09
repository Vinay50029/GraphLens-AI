import operator
import re
from typing import Annotated
from typing_extensions import TypedDict

from api.utils.llm_factory import get_llm
from api.rag.retrieve import get_retriever, get_vectorstore


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    active_documents: list[str]
    user_id: int


def document_node(state: AgentState):
    """Answers questions based on retrieved documents from Pinecone."""
    messages = state["messages"]
    question = messages[-1].content
    user_id = state.get("user_id")

    active_documents = state.get("active_documents") or []
    
    # 1. Detect if the user named explicit file name(s) in the question
    filename_matches = re.findall(r"([\w\-. ]+\.(?:pdf|txt))\b", question, flags=re.IGNORECASE)
    explicit_file_names = [f.strip() for f in filename_matches] if filename_matches else []
    
    scoped_file_names = explicit_file_names if explicit_file_names else active_documents

    # 2. Get retriever based on active/explicit documents, or globally if none is active
    retriever = get_retriever(user_id, scoped_file_names) if user_id else None
    
    docs = []
    if retriever:
        docs = retriever.invoke(question)

    # 3. Construct context text from retrieved document chunks, tagging each with its source
    if docs:
        context = "\n\n".join([f"[Source Document: {doc.metadata.get('file_name', 'Unknown')}]\n{doc.page_content}" for doc in docs])
    elif scoped_file_names:
        files_str = ", ".join(f"'{f}'" for f in scoped_file_names)
        context = f"No chunks were found for {files_str}. Please make sure the documents are ingested."
    else:
        context = "No documents have been loaded into the database yet. Please upload and ingest a document first."

    # 5. Format history and create final prompt for the LLM
    history_msgs = messages[-5:-1] if len(messages) > 1 else []
    conversation_history = ""
    if history_msgs:
        history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in history_msgs])
        conversation_history = f"Recent Conversation:\n{history_str}\n"

    prompt = f"""You are a helpful research assistant. Answer the user's question based strictly on the provided context.
Compare and synthesize information across multiple documents when relevant, noting the source document names in your analysis.
If the context doesn't contain the answer, say that you don't know based on the provided documents.

Context:
{context}

{conversation_history}
Question: {question}
"""

    llm = get_llm(temperature=0.2)
    response = llm.invoke(prompt)
    return {"messages": [response]}
