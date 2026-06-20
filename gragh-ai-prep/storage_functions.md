# 📂 Storage.py Functions: Student Interview Guide

This guide explains every function in [storage.py](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/utils/storage.py) in a simple, student-friendly way that is easy to talk about in an interview.

---

## 🔑 1. Connection & Path Helpers

### 1. `get_s3_client()`
* **What it does**: Sets up the connection to AWS S3 using our access credentials.
* **Student Answer**: 
  > "This function initializes and returns the `boto3` client. It checks if we have local AWS keys (`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`) and connects our code to S3."

### 2. `get_user_dir(user_id)`
* **What it does**: Generates a local folder path for a specific user and creates it if it doesn't exist.
* **Student Answer**: 
  > "This function resolves a local folder path under `media/users/[user_id]/`. It uses `os.makedirs` to automatically create the folder on the server if it is missing, helping us sandbox each user's files."

---

## 🔄 2. Document Conversion Helpers (Word & PDF)

### 3. `convert_text_to_docx(text)` & `convert_docx_to_text(file_bytes)`
* **What it does**: Converts plain text to Word files (.docx), and extracts plain text from Word binary files.
* **Student Answer**: 
  > "These two helper functions handle Word documents using the `python-docx` library:
  > * `convert_text_to_docx`: Takes raw text, creates a new document object, adds paragraphs line-by-line, and saves it as binary data.
  > * `convert_docx_to_text`: Reads raw binary file data and extracts the text so the LLM can read and analyze it."

### 4. `convert_text_to_pdf(text)` & `convert_pdf_to_text(file_bytes)`
* **What it does**: Converts plain text to PDF files, and extracts plain text from PDF binary files.
* **Student Answer**: 
  > "These functions handle PDF conversions:
  > * `convert_text_to_pdf`: Uses `fpdf2` to create a blank PDF, set the font, write the text in a multi-cell format, and return raw PDF bytes.
  > * `convert_pdf_to_text`: Uses `PyMuPDF` (`fitz`) to open the PDF, loop through pages, extract the text, and return it as a single string."

---

## 📂 3. File CRUD Operations

### 5. `write_user_file(user_id, filename, content)`
* **What it does**: Writes content (text or bytes) to a user's local folder AND uploads it to S3 (if enabled).
* **Student Answer**: 
  > "This is our file saver function. When called:
  > 1. It checks the filename extension. If it is `.pdf` or `.docx`, it automatically runs our conversion helpers to turn plain text into binary PDF/Word files.
  > 2. It saves the file locally in `media/users/[user_id]/`.
  > 3. If S3 is enabled (`USE_S3 = True`), it calls `s3.put_object()` to upload the file to S3 as a permanent backup."

### 6. `read_user_file(user_id, filename)`
* **What it does**: Reads and returns raw file bytes.
* **Student Answer**: 
  > "This is our file loader. It checks if the file is in the local folder. If S3 is enabled and the local file is missing (e.g. because Render restarted and wiped it), it calls `s3.get_object()` to download the file, saves a copy locally, and returns the file bytes."

### 7. `delete_user_file(user_id, filename)`
* **What it does**: Deletes the file from both local cache storage and AWS S3.
* **Student Answer**: 
  > "This function handles file deletion. It uses `os.remove` to delete the file from the server's local disk, and `s3.delete_object` to permanently delete it from AWS S3."

### 8. `list_user_files(user_id)`
* **What it does**: Lists all filenames in a user's directory.
* **Student Answer**: 
  > "This function retrieves all filenames owned by the user. If S3 is enabled, it calls `s3.list_objects_v2` with the user prefix. Otherwise, it falls back to listing files from the local directory using `os.listdir`."

### 9. `get_user_file_url(user_id, filename)`
* **What it does**: Generates a secure, shareable download/view link for a file.
* **Student Answer**: 
  > "This generates the download link:
  > * If S3 is enabled, it generates a secure, temporary **Presigned URL** that is valid for 1 hour.
  > * If S3 is disabled, it returns the standard local media path (`/media/users/...`)."

---

## 🧠 4. Deep-Dive Concepts (Interview Focus)

### Q1: Why use `get_user_dir(user_id)` if we are already storing files in AWS S3?
* **The Problem**: Cloud files stored in S3 are just links (URLs). Python text extraction libraries like `PyMuPDF` (for PDFs) and `python-docx` (for Word) cannot read or analyze files directly from a cloud URL. They need a physical file saved on the local hard drive to run their algorithms.
* **The Solution**: Before we read or index a file, we download it from S3 and write it temporarily to the server's local folder. `get_user_dir(user_id)` dynamically creates and locates this folder (`media/users/[user_id]/`) on the server so that we have a secure local sandbox to parse the file.

### Q2: Why do we create a "Document Object" and save it as "Binary Data" instead of standard text?
* **Why a Document Object?**
  A Microsoft Word file (`.docx`) is not a simple plain text file. Under the hood, it is actually a compressed folder containing XML files for formatting, font sizes, styles, and paragraphs. The Python library (`python-docx`) cannot just write text directly; it has to construct this complex XML folder structure. It does this by creating a `Document` object in memory and letting you add paragraphs to it.
* **Why save it as Binary Data?**
  * Plain text files (`.txt`) are written using standard text modes (`'w'`), which just save plain characters.
  * PDF and Word files are **binary files** (they contain compressed structures, layouts, and metadata). If you try to save a Word or PDF file as standard text, Python will try to decode it, which corrupts the file and makes it unreadable. We must write it as raw, unformatted binary data using `'wb'` (Write Binary) mode.

### Q3: Why do we use a "Blank PDF", "Multi-Cell format", and return it in "Bytes"?
* **Why a Blank PDF?**
  A PDF is like a blank drawing canvas. Unlike a text file where you just type characters, a PDF has no default text formatting, page margins, or page breaks. We must programmatically create a blank PDF page, select a font (like Helvetica), and choose a font size before we can print any words.
* **Why Multi-Cell format?**
  If you write a long paragraph in a PDF without wrapping, it will print in a single straight line and overflow off the right side of the page (you won't be able to read it). The `multi_cell()` function in the `fpdf2` library automatically wraps the text to the next line when it hits the right margin, creating formatted paragraphs.
* **Why returning in Bytes?**
  Instead of saving the file to the local hard drive first and then reading it back (which is slow), we generate the PDF entirely in the computer's RAM as raw bytes. This allows us to instantly upload it to AWS S3 and save it to the local cache simultaneously in a fraction of a millisecond.

### Q4: Why can't we read PDF or Word files directly as text without libraries like PyMuPDF or python-docx?
* **Student Answer**: 
  > "If you open a PDF or Word file in a plain text editor, it looks like a mountain of scrambled binary garbage (styling codes, margins, page geometry, and compression headers). 
  > 
  > We MUST use libraries like `PyMuPDF` or `python-docx` because they act as **translators**:
  > 1. They **unzip** the compressed text streams.
  > 2. They **strip away** all styling codes (like font colors, margins, and coordinate math).
  > 3. They **extract only** clean, human-readable text (e.g. *'Q3 Revenue is $10M'*).
  > 
  > Without these libraries, Python would read raw layout garbage, send it to the LLM, and the LLM would not be able to understand it."

---

## 🗄️ 5. Underlying Storage & Parsing Architecture

### 1. Underlying Storage (On disk or S3)
No matter the file type, everything is written to disk (and uploaded to AWS S3) in binary mode (`'wb'`) as bytes. However, the bytes representing them are formatted differently based on the extension:

* **Text Files (`.txt`):** The plain text string is encoded directly to UTF-8 bytes (`content.encode('utf-8')`) and saved. It remains human-readable if you open the raw file directly.
* **Word Documents (`.docx` / `.doc`):** The plain text is compiled into a valid `.docx` zip package structure containing XML using the `python-docx` library via [convert_text_to_docx](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/utils/storage.py#L34).
* **PDF Documents (`.pdf`):** The plain text is compiled into a valid formatted PDF binary structure using the `fpdf2` library via [convert_text_to_pdf](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/utils/storage.py#L56).

### 2. Reading and Parsing
When the Workspace File Agent reads a file (defined in [read_file](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/file_agent.py#L95)), it reads the raw binary bytes and extracts the text representation differently depending on the file type:

* **`.txt`:** Decodes the UTF-8 bytes directly to a readable string:
  ```python
  text = content_bytes.decode('utf-8', errors='ignore')
  ```

* **`.docx` / `.doc`:** Extracts paragraphs from the binary structure using `docx`:
  ```python
  doc = docx.Document(io.BytesIO(file_bytes))
  text = '\n'.join([para.text for para in doc.paragraphs])
  ```

* **`.pdf`:** Extracts textual content page-by-page from the binary PDF structure using PyMuPDF (`fitz`):
  ```python
  doc = fitz.open(stream=file_bytes, filetype="pdf")
  text = '\n'.join([page.get_text() for page in doc])
  ```



