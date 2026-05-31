import os
import io
import docx
import fitz
from fpdf import FPDF
from django.conf import settings
from pathlib import Path

def get_user_dir(user_id: int) -> Path:
    """Returns the Path directory for a specific user's files."""
    user_dir = Path(settings.MEDIA_ROOT) / "users" / str(user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

# --- Word Document Binary Conversion Helpers ---

def convert_text_to_docx(text: str) -> bytes:
    """Creates a valid .docx binary from plain text."""
    doc = docx.Document()
    for line in text.split('\n'):
        doc.add_paragraph(line)
    
    file_stream = io.BytesIO()
    doc.save(file_stream)
    return file_stream.getvalue()

def convert_docx_to_text(file_bytes: bytes) -> str:
    """Extracts raw text from a .docx binary."""
    doc = docx.Document(io.BytesIO(file_bytes))
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)

# --- PDF Document Binary Conversion Helpers ---

def convert_text_to_pdf(text: str) -> bytes:
    """Creates a valid .pdf binary from plain text using fpdf2."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, text=text)
    return bytes(pdf.output())

def convert_pdf_to_text(file_bytes: bytes) -> str:
    """Extracts raw text from a .pdf binary using PyMuPDF."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = []
        for page in doc:
            text.append(page.get_text())
        doc.close()
        return "\n".join(text)
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"

# ------------------------------------------------

def write_user_file(user_id: int, filename: str, content) -> int:
    """
    Writes file content (str or bytes) to user's folder.
    Automatically converts text to valid Word .docx binary if filename is .doc/.docx.
    Automatically converts text to valid PDF binary if filename is .pdf.
    Returns: file size in bytes.
    """
    is_word_doc = filename.lower().endswith(('.docx', '.doc'))
    is_pdf_doc = filename.lower().endswith('.pdf')

    if is_word_doc and isinstance(content, str):
        try:
            file_bytes = convert_text_to_docx(content)
        except Exception:
            file_bytes = content.encode('utf-8')
    elif is_pdf_doc and isinstance(content, str):
        try:
            file_bytes = convert_text_to_pdf(content)
        except Exception:
            file_bytes = content.encode('utf-8')
    elif isinstance(content, str):
        file_bytes = content.encode('utf-8')
    else:
        file_bytes = content

    user_dir = get_user_dir(user_id)
    file_path = user_dir / filename
    
    with open(file_path, 'wb') as f:
        f.write(file_bytes)
        
    return len(file_bytes)

def read_user_file(user_id: int, filename: str) -> bytes:
    """Reads file content from the user's folder."""
    user_dir = get_user_dir(user_id)
    file_path = user_dir / filename
    
    with open(file_path, 'rb') as f:
        return f.read()

def delete_user_file(user_id: int, filename: str):
    """Deletes a file from the user's folder."""
    user_dir = get_user_dir(user_id)
    file_path = user_dir / filename
    if file_path.exists():
        os.remove(file_path)

def list_user_files(user_id: int) -> list[str]:
    """Lists the filenames in the user's folder."""
    user_dir = get_user_dir(user_id)
    try:
        return [f for f in os.listdir(user_dir) if os.path.isfile(user_dir / f)]
    except FileNotFoundError:
        return []

import urllib.parse

def get_user_file_url(user_id: int, filename: str) -> str:
    """Returns the media URL path for a user's file."""
    encoded_filename = urllib.parse.quote(filename)
    return f"{settings.MEDIA_URL}users/{user_id}/{encoded_filename}"