import os
import tempfile
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from langchain_core.messages import HumanMessage, AIMessage

from api.graph.workflow import create_workflow
from api.rag.ingest import ingest_documents

# ─── Lazy-loaded workflow (created once, reused) ──────────────────────────────
_workflow = None

def get_workflow():
    global _workflow
    if _workflow is None:
        _workflow = create_workflow()
    return _workflow


# ─── Helper to deserialize messages from JSON ────────────────────────────────
def deserialize_messages(raw_messages: list) -> list:
    """Converts [{ role: 'user'|'assistant', content: '...' }] → LangChain messages."""
    messages = []
    for m in raw_messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    return messages


# ─── ENDPOINT 1: Health Check ─────────────────────────────────────────────────
@api_view(["GET"])
def health(request):
    """Simple health check endpoint."""
    return Response({"status": "ok", "message": "Intelligent Research Assistant API is running."})


# ─── ENDPOINT 2: Chat ─────────────────────────────────────────────────────────
@api_view(["POST"])
def chat(request):
    """
    Accepts a conversation history and returns the AI's next response.

    Request body (JSON):
    {
        "messages": [
            { "role": "user", "content": "What is in my document?" },
            { "role": "assistant", "content": "Your document contains..." },
            { "role": "user", "content": "Tell me more." }
        ]
    }

    Response:
    {
        "role": "assistant",
        "content": "Here is what I found..."
    }
    """
    raw_messages = request.data.get("messages", [])
    if not raw_messages:
        return Response(
            {"error": "No messages provided."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        lc_messages = deserialize_messages(raw_messages)
        workflow = get_workflow()

        active_document = request.data.get("active_document")
        final_state = workflow.invoke(
            {"messages": lc_messages, "active_document": active_document or ""}
        )
        ai_response = final_state["messages"][-1]

        return Response({
            "role": "assistant",
            "content": ai_response.content,
        })

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ─── ENDPOINT 3: Ingest PDF ───────────────────────────────────────────────────
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def ingest(request):
    """
    Accepts a PDF file upload, ingests it into Pinecone, and returns the result.

    Request: multipart/form-data with a 'file' field (PDF only, max 200 MB)

    Response:
    {
        "success": true,
        "message": "Successfully ingested 42 chunks from 10 pages into Pinecone.",
        "chunks": 42,
        "pages": 10
    }
    """
    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return Response(
            {"error": "No file provided. Send a PDF in the 'file' field."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not uploaded_file.name.lower().endswith(".pdf"):
        return Response(
            {"error": "Only PDF files are supported."},
            status=status.HTTP_400_BAD_REQUEST
        )

    max_size = 200 * 1024 * 1024  # 200 MB
    if uploaded_file.size > max_size:
        return Response(
            {"error": "File is too large. Maximum allowed size is 200 MB."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Save to a temporary file, then ingest
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        result = ingest_documents(tmp_path, original_file_name=uploaded_file.name)
    except Exception as e:
        return Response(
            {"success": False, "error": f"Ingestion failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    finally:
        # Always clean up the temp file when it exists
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    if result.get("success"):
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
