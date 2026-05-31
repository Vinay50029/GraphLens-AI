import os
import tempfile
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from langchain_core.messages import HumanMessage, AIMessage

from api.graph.workflow import create_workflow
from api.rag.ingest import ingest_documents, delete_document_index
from api.models import UserFile
from api.utils.storage import write_user_file, delete_user_file, get_user_file_url


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


# ─── HTML Page Views (Standard Django Views) ───────────────────────────────────

def signup_view(request):
    """Renders the sign-up page and handles user creation."""
    if request.user.is_authenticated:
        return redirect('chat_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not username or not email or not password:
            return render(request, 'signup.html', {'error': 'All fields are required.'})

        # Validate Email Format
        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'signup.html', {'error': 'Invalid email address format.'})

        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already taken.'})

        try:
            # Create user and log them in
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('chat_dashboard')
        except Exception as e:
            return render(request, 'signup.html', {'error': f'Failed to create account: {str(e)}'})

    return render(request, 'signup.html')


def login_view(request):
    """Renders the login page and handles authentication."""
    if request.user.is_authenticated:
        return redirect('chat_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('chat_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password.'})

    return render(request, 'login.html')


def logout_view(request):
    """Logs out the user and redirects to login."""
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def chat_view(request):
    """Renders the main dashboard page."""
    return render(request, 'chat.html')


# ─── JSON API Endpoints (DRF Views) ───────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Simple health check endpoint."""
    return Response({"status": "ok", "message": "Intelligent Research Assistant API is running."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    Accepts a conversation history and returns the AI's next response.
    Saves and filters file/document retrieval context for request.user.id.
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
        
        # Invoke workflow passing user_id for multi-tenancy scoping
        final_state = workflow.invoke({
            "messages": lc_messages, 
            "active_document": active_document or "",
            "user_id": request.user.id
        })
        ai_response = final_state["messages"][-1]

        return Response({
            "role": "assistant",
            "content": ai_response.content,
        })

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate_limit" in error_msg or "rate limit" in error_msg.lower():
            friendly_msg = "Rate limit reached! Please try again in a few minutes."
        else:
            friendly_msg = error_msg
            
        return Response(
            {"error": friendly_msg},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def ingest(request):
    """
    Accepts a PDF, Word (.doc/.docx), or Text (.txt) upload, embeds/indexes it in Pinecone,
    saves the file to standard user storage, and registers it in the DB.
    """
    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return Response(
            {"error": "No file provided. Please send a valid document in the 'file' field."},
            status=status.HTTP_400_BAD_REQUEST
        )

    allowed_exts = (".pdf", ".docx", ".doc", ".txt")
    filename_lower = uploaded_file.name.lower()
    if not filename_lower.endswith(allowed_exts):
        return Response(
            {"error": "Only PDF, Word (.doc, .docx), and Text (.txt) files are supported for Q&A ingestion."},
            status=status.HTTP_400_BAD_REQUEST
        )

    max_size = 200 * 1024 * 1024  # 200 MB
    if uploaded_file.size > max_size:
        return Response(
            {"error": "File is too large. Maximum allowed size is 200 MB."},
            status=status.HTTP_400_BAD_REQUEST
        )

    tmp_path = None
    try:
        # Preserve original extension in temp file name for loader dispatching
        _, ext = os.path.splitext(uploaded_file.name)
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        # Ingest documents tagged with user_id into Pinecone
        result = ingest_documents(tmp_path, user_id=request.user.id, original_file_name=uploaded_file.name)
        
        if result.get("success"):
            # Write file to local storage so it is download-accessible
            uploaded_file.seek(0)
            file_content = uploaded_file.read()
            write_user_file(request.user.id, uploaded_file.name, file_content)

            # Register in UserFile DB
            user_file, created = UserFile.objects.get_or_create(
                user=request.user,
                filename=uploaded_file.name,
                defaults={'file_size': uploaded_file.size}
            )
            if not created:
                user_file.file_size = uploaded_file.size
                user_file.save()

            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response(
            {"success": False, "error": f"Ingestion failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_files_api(request):
    """Lists the files metadata uploaded by the current user."""
    files = UserFile.objects.filter(user=request.user).order_by('-created_at')
    data = []
    for f in files:
        data.append({
            "id": f.id,
            "filename": f.filename,
            "file_size": f.file_size,
            "created_at": f.created_at.isoformat(),
            "url": get_user_file_url(request.user.id, f.filename)
        })
    return Response({"files": data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_file_api(request):
    """Saves an uploaded file to the user's isolated storage prefix and logs it in the DB (no vector indexing)."""
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return Response({"error": "No file uploaded in 'file' field"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        content = uploaded_file.read()
        size = write_user_file(request.user.id, uploaded_file.name, content)
        
        user_file, created = UserFile.objects.get_or_create(
            user=request.user,
            filename=uploaded_file.name,
            defaults={'file_size': size}
        )
        if not created:
            user_file.file_size = size
            user_file.save()
            
        return Response({
            "success": True, 
            "filename": uploaded_file.name, 
            "size": size,
            "url": get_user_file_url(request.user.id, uploaded_file.name)
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_file_api(request, file_id):
    """Deletes a file record from the DB and its corresponding storage object."""
    try:
        user_file = UserFile.objects.get(id=file_id, user=request.user)
    except UserFile.DoesNotExist:
        return Response({"error": "File not found or permission denied."}, status=status.HTTP_404_NOT_FOUND)
        
    try:
        filename = user_file.filename
        user_file.delete()
        delete_user_file(request.user.id, filename)
        
        # Purge vectors from Pinecone as well
        delete_document_index(request.user.id, filename)
        
        return Response({"success": True, "message": f"Successfully deleted file '{filename}'."})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
