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
    
    import os

    # 1. Detect if the user named explicit file name(s) in the question
    filename_matches = re.findall(r"([\w\-. ]+\.(?:pdf|txt))\b", question, flags=re.IGNORECASE)
    explicit_file_names = [f.strip() for f in filename_matches] if filename_matches else []
    
    # Check for matching active_documents by base name (without extension) if no exact extensions matched
    if not explicit_file_names and active_documents:
        for doc in active_documents:
            base_name = os.path.splitext(doc)[0]
            pattern = r"\b" + re.escape(base_name) + r"\b"
            if re.search(pattern, question, flags=re.IGNORECASE):
                explicit_file_names.append(doc)

    scoped_file_names = explicit_file_names if explicit_file_names else active_documents

    # Clean the query by stripping explicit filename references to avoid vector search bias
    clean_question = question
    for fname in scoped_file_names:
        clean_question = re.sub(re.escape(fname), "", clean_question, flags=re.IGNORECASE)
        base_name = os.path.splitext(fname)[0]
        clean_question = re.sub(r"\b" + re.escape(base_name) + r"\b", "", clean_question, flags=re.IGNORECASE)
    
    clean_question = re.sub(r"\b(using|of|in|about|from|the|with|compare|pdfs|pdf)\b", "", clean_question, flags=re.IGNORECASE)
    clean_question = re.sub(r"\s+", " ", clean_question).strip()
    if not clean_question:
        clean_question = question

    # 2. Retrieve documents from the active vector store
    docs = []
    if user_id:
        if len(scoped_file_names) > 1:
            # Query each file separately to ensure balanced context representation
            for fname in scoped_file_names:
                file_retriever = get_retriever(user_id, fname)
                if file_retriever:
                    file_retriever.search_kwargs["k"] = max(3, 12 // len(scoped_file_names))
                    try:
                        docs.extend(file_retriever.invoke(clean_question))
                    except Exception as e:
                        print(f"Error retrieving from file {fname}: {e}")
        else:
            retriever = get_retriever(user_id, scoped_file_names)
            if retriever:
                try:
                    docs = retriever.invoke(clean_question)
                except Exception as e:
                    print(f"Error invoking retriever: {e}")

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
