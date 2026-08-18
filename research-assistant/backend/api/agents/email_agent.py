import operator
from typing import Annotated, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from langchain_core.messages import AIMessage
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth.models import User

from api.models import UserFile
from api.utils.storage import read_user_file
from api.utils.llm_factory import get_llm


# ─── 1. Agent State Definition ────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    active_documents: list[str]
    user_id: int
    user_email: Optional[str]
    user_name: Optional[str]


# ─── 2. Input Schema for Parameter Extraction ─────────────────────────────────

class EmailInput(BaseModel):
    recipient_email: str = Field(..., description="Target email address to send to")
    filename: Optional[str] = Field(None, description="Name of the file to attach")


# ─── 3. Helper Function to Send Email ─────────────────────────────────────────

def send_user_email(user_id: int, recipient_email: str, filename: Optional[str], active_documents: list[str], user_email: str, user_name: str) -> str:
    """Simple function to find the requested file and send an email with attachment."""
    
    # Get all file names for this user
    user_files = list(UserFile.objects.filter(user_id=user_id).values_list('filename', flat=True))
    
    # Find matching file
    target_file = None
    if filename:
        req = filename.lower().replace("the ", "").strip()
        for f in user_files:
            if req in f.lower():
                target_file = f
                break
    
    # Fallback to active document if not specified
    if not target_file and active_documents:
        target_file = active_documents[0]
    elif not target_file and user_files:
        target_file = user_files[0]

    if not target_file:
        return "Error: No file found in your workspace to send."

    # Read file content from storage
    try:
        file_bytes = read_user_file(user_id, target_file)
    except Exception as e:
        return f"Error reading file '{target_file}': {str(e)}"

    # Construct and send email using Django EmailMessage
    subject = f"{user_name} shared a document with you: {target_file}"
    body = (
        f"Hello,\n\n"
        f"{user_name} ({user_email}) has shared a document with you via GraphLens AI.\n\n"
        f"📄 Attached Document: {target_file}\n\n"
        f"--------------------------------------------------\n"
        f"Sent on behalf of {user_name} ({user_email}) by GraphLens AI.\n"
        f"Replying to this email will send your message directly to {user_email}.\n"
    )
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'GraphLens AI <intelligentresearchassistant@gmail.com>')
    
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=[recipient_email],
        reply_to=[user_email] if "@" in user_email else None
    )
    
    # Attach PDF file
    email.attach(target_file, file_bytes, "application/pdf")
    
    try:
        email.send(fail_silently=False)
        return (
            f"✅ Successfully sent email to '{recipient_email}'!\n"
            f"• Attached File: {target_file}\n"
            f"• Sender Identified As: {user_name} ({user_email})\n"
            f"• Reply-To Address: {user_email}"
        )
    except Exception as e:
        return f"Error sending email: {str(e)}"


# ─── 4. LangGraph Node Function ───────────────────────────────────────────────

def email_node(state: AgentState):
    """Simple Email Agent Node that extracts details and sends email."""
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    user_id = state.get("user_id")
    active_documents = state.get("active_documents") or []
    
    # Get user details
    user_email = state.get("user_email")
    user_name = state.get("user_name")
    if user_id:
        try:
            u = User.objects.get(id=user_id)
            user_email = user_email or u.email
            user_name = user_name or u.username
        except User.DoesNotExist:
            pass
            
    user_email = user_email or "user@gmail.com"
    user_name = user_name or "User"

    # Get available files list
    user_files = list(UserFile.objects.filter(user_id=user_id).values_list('filename', flat=True)) if user_id else []
    
    # Extract recipient and filename from query using LLM
    llm = get_llm(temperature=0.0)
    extractor = llm.with_structured_output(EmailInput)
    
    prompt = f"""Extract the recipient email address and file name from the user request.
    Available Files: {user_files}
    Active File: {active_documents}
    User Request: {last_message}
    """
    
    try:
        data = extractor.invoke(prompt)
        result = send_user_email(
            user_id=user_id,
            recipient_email=data.recipient_email,
            filename=data.filename,
            active_documents=active_documents,
            user_email=user_email,
            user_name=user_name
        )
    except Exception as e:
        result = f"Failed to send email: {str(e)}"

    return {"messages": [AIMessage(content=result)]}
