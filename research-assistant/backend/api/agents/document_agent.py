import operator
import re
from typing import Annotated, List, Optional
from typing_extensions import TypedDict

from api.utils.llm_factory import get_llm
from api.rag.retrieve import get_retriever, get_vectorstore


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    active_document: str


def _tokenize_for_match(text: str) -> List[str]:
    lowered = text.lower()
    tokens = []

    # Words (keep 2+ chars so short acronyms like "ml" still participate when typed lowercase)
    tokens.extend(re.findall(r"[a-z0-9]{2,}", lowered))

    # ALLCAPS acronyms in the original text (e.g., PCA, SVM)
    tokens.extend([t.lower() for t in re.findall(r"\b[A-Z]{2,}\b", text)])

    # De-hyphenate common compound tokens
    extra = []
    for t in list(tokens):
        if "-" in t:
            extra.extend([p for p in t.split("-") if len(p) >= 2])
    tokens.extend(extra)

    # De-dupe while preserving rough order
    seen = set()
    out = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _question_tokens(question: str) -> List[str]:
    stop = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "what",
        "your",
        "you",
        "can",
        "tell",
        "about",
        "how",
        "why",
        "when",
        "where",
        "does",
        "did",
        "are",
        "was",
        "were",
        "into",
        "using",
        "use",
    }
    return [t for t in _tokenize_for_match(question) if t not in stop]


def _context_supports_question(question: str, context: str) -> bool:
    q_tokens = _question_tokens(question)
    if not q_tokens:
        return True
    ctx = (context or "").lower()
    hits = sum(1 for t in q_tokens if t in ctx)
    return hits >= max(1, min(2, len(q_tokens) // 2))


def _merge_retrievals(
    retriever,
    queries: List[str],
    max_docs: int,
) -> List:
    seen = set()
    docs = []
    for query in queries:
        for doc in retriever.invoke(query):
            key = (doc.page_content or "").strip()
            if key and key not in seen:
                seen.add(key)
                docs.append(doc)
            if len(docs) >= max_docs:
                return docs
    return docs


def _mmr_search(
    vectorstore,
    query: str,
    file_name: Optional[str],
    k: int,
    fetch_k: int,
) -> List:
    if not vectorstore:
        return []
    kwargs = {}
    if file_name:
        kwargs["filter"] = {"file_name": {"$eq": file_name}}
    return vectorstore.max_marginal_relevance_search(query, k=k, fetch_k=fetch_k, **kwargs)


def _merge_mmr(
    vectorstore,
    queries: List[str],
    file_name: Optional[str],
    k_per_query: int,
    fetch_k: int,
    max_docs: int,
) -> List:
    seen = set()
    docs = []
    for query in queries:
        for doc in _mmr_search(vectorstore, query, file_name, k=k_per_query, fetch_k=fetch_k):
            key = (doc.page_content or "").strip()
            if key and key not in seen:
                seen.add(key)
                docs.append(doc)
            if len(docs) >= max_docs:
                return docs
    return docs


def document_node(state: AgentState):
    """Answers questions based on retrieved documents from Pinecone."""
    messages = state["messages"]
    question = messages[-1].content

    active_document = (state.get("active_document") or "").strip() or None
    filename_match = re.search(r"([\w\-. ]+\.pdf)\b", question, flags=re.IGNORECASE)
    explicit_file_name = filename_match.group(1).strip() if filename_match else None

    # If user names a PDF explicitly, always prefer that filter.
    scoped_file_name = explicit_file_name or active_document

    vectorstore = get_vectorstore()
    retriever_scoped = get_retriever(scoped_file_name)
    retriever_global = get_retriever(None)

    if retriever_scoped or retriever_global:
        summary_like = any(
            token in question.lower()
            for token in ["summarize", "summary", "overview", "entire", "whole pdf", "key points"]
        )
        queries = [question]
        if summary_like:
            queries.extend(
                [
                    "overall summary, objectives, methodology, key findings, conclusion",
                    "main topics, important details, and takeaways from the document",
                ]
            )

        docs = []
        context_mode = "none"

        # 1) Scoped retrieval (active/explicit PDF) when possible
        if scoped_file_name and retriever_scoped:
            docs = _merge_retrievals(retriever_scoped, queries, max_docs=12)
            context_mode = "scoped"
        elif (not scoped_file_name) and retriever_global:
            docs = _merge_retrievals(retriever_global, queries, max_docs=12)
            context_mode = "global"

        # 2) If scoped retrieval looks empty OR doesn't seem to contain the question topic,
        # widen search across all ingested vectors (unless user explicitly pinned a filename).
        scoped_context = "\n\n".join([d.page_content for d in docs])
        should_widen = (not explicit_file_name) and (
            (scoped_file_name and not docs)
            or (bool(docs) and not _context_supports_question(question, scoped_context))
        )

        if should_widen and retriever_global:
            global_docs = _merge_retrievals(retriever_global, queries, max_docs=12)
            # Prefer global results if they actually match better
            global_context = "\n\n".join([d.page_content for d in global_docs])
            if global_docs and _context_supports_question(question, global_context):
                docs = global_docs
                context_mode = "global"
            elif not docs:
                docs = global_docs
                context_mode = "global"

        # 3) Last resort: pull extra breadth via direct MMR against vectorstore
        if (not docs) and vectorstore:
            docs = _merge_mmr(
                vectorstore,
                queries,
                file_name=scoped_file_name if scoped_file_name and not should_widen else None,
                k_per_query=8,
                fetch_k=48,
                max_docs=16,
            )
            context_mode = "mmr_fallback"

        if scoped_file_name and not docs:
            context = (
                f"No chunks were found for '{scoped_file_name}'. "
                "Please re-ingest this PDF so it can be linked to document-aware retrieval."
            )
        else:
            context = "\n\n".join([doc.page_content for doc in docs])
            if context_mode == "global" and scoped_file_name and not explicit_file_name:
                context = (
                    f"(Search note: widened retrieval across all ingested PDFs because '{scoped_file_name}' "
                    f"did not appear to contain a good match for this question.)\n\n{context}"
                )
    else:
        context = "No documents have been loaded into the database yet. Please upload and ingest a PDF first."

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
