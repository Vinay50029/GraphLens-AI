import operator
from typing import Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from django.contrib.auth.models import User
from api.models import UserFile
from api.utils.storage import write_user_file, read_user_file, delete_user_file, list_user_files
from api.utils.llm_factory import get_llm
from api.rag.ingest import ingest_documents, delete_document_index

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    active_document: str
    user_id: int

# --- Pydantic Schemas for Tool Arguments ---
class CreateFileInput(BaseModel):
    filename: str = Field(..., description="The name of the file to create, e.g. notes.txt")
    content: str = Field(..., description="The text content to write into the file")

class ReadFileInput(BaseModel):
    filename: str = Field(..., description="The name of the file to read, e.g. notes.txt")

class UpdateFileInput(BaseModel):
    filename: str = Field(..., description="The name of the file to update, e.g. notes.txt")
    content: str = Field(..., description="The new text content to add or replace")
    mode: str = Field(..., description="The update mode: must be either 'append' or 'overwrite'")

class DeleteFileInput(BaseModel):
    filename: str = Field(..., description="The name of the file to delete, e.g. notes.txt")

class ListFilesInput(BaseModel):
    filter_extension: str = Field("", description="Optional extension to filter by, e.g. .txt")


# --- Boilerplate Helper ---
def _get_user_and_filename(config: RunnableConfig, filename: str):
    """Utility to authenticate user and enforce the active document if selected in UI."""
    user_id = config.get("configurable", {}).get("user_id")
    active_document = (config.get("configurable", {}).get("active_document") or "").strip()
    last_message = (config.get("configurable", {}).get("last_message") or "").strip()
    
    if not user_id:
        raise ValueError("No user authenticated. Cannot perform file operations.")
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError("Authenticated user does not exist in the database.")

    # Enforce active document ONLY if:
    # 1. An active document is selected in UI.
    # 2. The user did NOT explicitly mention the target filename in their message.
    if active_document and filename != active_document:
        import os
        base_name = os.path.splitext(filename)[0].lower()
        if base_name not in last_message.lower() and filename.lower() not in last_message.lower():
            filename = active_document
        
    return user, filename


# --- Global Tools ---

@tool(args_schema=CreateFileInput)
def create_file(filename: str, content: str, config: RunnableConfig) -> str:
    """Creates a new file. If the file already exists, it will overwrite it."""
    try:
        original_filename = filename
        user, filename = _get_user_and_filename(config, filename)
        
        allowed_extensions = (".pdf", ".txt")
        if not filename.lower().endswith(allowed_extensions):
            return f"Error: Invalid file extension. Only PDF (.pdf) and text (.txt) files are supported in this workspace."
            
        user_file, created = UserFile.objects.get_or_create(user=user, filename=filename)
        size = write_user_file(user.id, filename, content)
        user_file.file_size = size
        user_file.save()
        
        # Auto-ingest to Pinecone
        if filename.lower().endswith((".txt", ".pdf")):
            try:
                from api.utils.storage import get_user_dir
                ingest_documents(str(get_user_dir(user.id) / filename), user_id=user.id, original_file_name=filename)
            except Exception as e:
                print(f"Failed to auto-ingest: {e}")
                
        msg = f"Successfully {'created' if created else 'overwritten'} file '{filename}' ({size} bytes)."
        if original_filename != filename:
            msg = f"Note: Enforced operation on the currently selected file '{filename}' instead of '{original_filename}'.\n" + msg
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@tool(args_schema=ReadFileInput)
def read_file(filename: str, config: RunnableConfig) -> str:
    """Reads and returns the content of the specified file."""
    try:
        original_filename = filename
        user, filename = _get_user_and_filename(config, filename)
        
        allowed_extensions = (".pdf", ".txt")
        if not filename.lower().endswith(allowed_extensions):
            return f"Error: Invalid file extension. Only PDF (.pdf) and text (.txt) files are supported in this workspace."
            
        if not UserFile.objects.filter(user=user, filename=filename).exists():
            return f"File '{filename}' does not exist."
            
        content_bytes = read_user_file(user.id, filename)
        
        # Parse based on file type
        if filename.lower().endswith('.pdf'):
            from api.utils.storage import convert_pdf_to_text
            text = convert_pdf_to_text(content_bytes)
            if len(text) > 10000:
                text = text[:10000] + "\n\n[Content truncated for brevity.]"
        else:
            text = content_bytes.decode('utf-8', errors='ignore')
            
        msg = f"Content of '{filename}':\n\n{text}"
        if original_filename != filename:
            msg = f"Note: Enforced operation on the currently selected file '{filename}' instead of '{original_filename}'.\n" + msg
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@tool(args_schema=UpdateFileInput)
def update_file(filename: str, content: str, mode: str, config: RunnableConfig) -> str:
    """Updates an existing file by appending or overwriting."""
    try:
        original_filename = filename
        user, filename = _get_user_and_filename(config, filename)
        
        allowed_extensions = (".pdf", ".txt")
        if not filename.lower().endswith(allowed_extensions):
            return f"Error: Invalid file extension. Only PDF (.pdf) and text (.txt) files are supported in this workspace."
            
        query = UserFile.objects.filter(user=user, filename=filename)
        if not query.exists():
            return f"File '{filename}' does not exist. Create it first."
        
        existing_content = ""
        if mode == 'append':
            try:
                content_bytes = read_user_file(user.id, filename)
                if filename.lower().endswith('.pdf'):
                    from api.utils.storage import convert_pdf_to_text
                    existing_content = convert_pdf_to_text(content_bytes)
                else:
                    existing_content = content_bytes.decode('utf-8', errors='ignore')
            except Exception:
                pass
        
        new_content = existing_content + content if mode == 'append' else content
        size = write_user_file(user.id, filename, new_content)
        
        user_file = query.first()
        user_file.file_size = size
        user_file.save()
        
        # Auto-ingest to Pinecone
        if filename.lower().endswith((".txt", ".pdf")):
            try:
                from api.utils.storage import get_user_dir
                ingest_documents(str(get_user_dir(user.id) / filename), user_id=user.id, original_file_name=filename)
            except Exception as e:
                print(f"Failed to auto-ingest: {e}")
                
        msg = f"Successfully updated file '{filename}' (size: {size} bytes) using mode '{mode}'."
        if original_filename != filename:
            msg = f"Note: Enforced operation on the currently selected file '{filename}' instead of '{original_filename}'.\n" + msg
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@tool(args_schema=DeleteFileInput)
def delete_file(filename: str, config: RunnableConfig) -> str:
    """Deletes a file from storage and purges it from RAG index."""
    try:
        original_filename = filename
        user, filename = _get_user_and_filename(config, filename)
        query = UserFile.objects.filter(user=user, filename=filename)
        if not query.exists():
            return f"File '{filename}' does not exist."
            
        query.delete()
        delete_user_file(user.id, filename)
        delete_document_index(user.id, filename)
        
        msg = f"Successfully deleted file '{filename}'."
        if original_filename != filename:
            msg = f"Note: Enforced operation on the currently selected file '{filename}' instead of '{original_filename}'.\n" + msg
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@tool(args_schema=ListFilesInput)
def list_files(config: RunnableConfig, filter_extension: str = "") -> str:
    """List the filenames currently in storage."""
    try:
        user_id = config.get("configurable", {}).get("user_id") if config else None
        if not user_id:
            return "Error: No user authenticated."
            
        files = list_user_files(user_id)
        if filter_extension:
            files = [f for f in files if f.lower().endswith(filter_extension.lower())]
            
        if not files:
            return "Storage is empty."
        return "Files:\n" + "\n".join([f"- {f}" for f in files])
    except Exception as e:
        return f"Error: {str(e)}"


# Build the React agent executor once globally
_llm = get_llm(temperature=0.0)
_agent_executor = create_react_agent(
    _llm, 
    tools=[create_file, read_file, update_file, delete_file, list_files]
)


def file_node(state: AgentState):
    """File manager agent node - invokes the file assistant executor."""
    user_id = state.get("user_id")
    active_document = (state.get("active_document") or "").strip()
    
    if not user_id:
        return {"messages": [AIMessage(content="Error: No user authenticated.")]}
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"messages": [AIMessage(content="Error: Authenticated user does not exist in the database.")]}

    active_doc_prompt = ""
    if active_document:
        active_doc_prompt = f"\nIMPORTANT: The user currently has the file '{active_document}' selected in the UI. If they refer to 'this file', 'the file', or do not specify another name, target '{active_document}'. If they explicitly ask to create or manage a different file by name (e.g. 'jhon.pdf'), you must target that name instead."

    system_prompt = SystemMessage(content=f"""You are a helpful AI file assistant for user '{user.username}'.{active_doc_prompt}
You have tools to create, read, update, delete, and list the user's files.
Only PDF (.pdf) and text (.txt) files are supported in this workspace. Word documents (.doc, .docx) and other formats are not supported.
Perform ONLY the specific operation requested by the user. Do not call any tools that are not directly requested.
Once you obtain the result from the tool, explain it to the user and stop. Do NOT call any more tools.
""")

    inputs = {"messages": [system_prompt] + state["messages"]}
    result = _agent_executor.invoke(
        inputs,
        config={
            "configurable": {
                "user_id": user_id,
                "active_document": active_document,
                "last_message": state["messages"][-1].content
            }
        }
    )
    return {"messages": [result["messages"][-1]]}