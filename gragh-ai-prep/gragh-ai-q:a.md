# 🎓 GraphLens AI: Student-Friendly Interview Guide

This guide contains simplified, clear, and easy-to-explain answers for your interview. They are written from a **student's perspective**—simple to understand, free of unnecessary jargon, but still technically accurate and impressive to interviewers.

---

## 🧠 1. Agent Orchestration & LangGraph

### Q1: Why did you use LangGraph instead of a simple sequential LLM chain?
* **Student Answer**: 
  > "A simple sequential chain only goes in one direction (Step A $\rightarrow$ Step B $\rightarrow$ Step C). But a research assistant is dynamic: the user might ask to search the web, then read a file, then ask a follow-up question. 
  > 
  > I used **LangGraph** because it lets us build a cyclic flowchart (a state machine). It keeps a central 'state' (like the chat history and active document) and routes the user's question to the right agent (Document Q&A, Web Search, or File Manager) depending on what the user wants to do."

### Q2: How does the supervisor routing mechanism work in simple terms?
* **Student Answer**: 
  > "The supervisor is like a traffic controller. When the user sends a message, it goes through a two-step check:
  > 
  > 1. **Quick Keyword Check**: First, we check the query for basic keywords (like 'create a file' or '.txt' or 'search'). If we find them, we route to the File Agent or Web Agent immediately without calling the LLM. This makes it fast and saves API costs.
  > 2. **LLM Routing**: If keywords don't match, we ask a router LLM (Groq) to classify the query into one of three roles: document search, web search, or file operation. We use a structured output format (Pydantic JSON) so the LLM responds with a clean classification instead of a long explanation."

### Q3: How do you prevent the conversation history from getting too long for the LLM?
* **Student Answer**: 
  > "If we send the entire chat history to the LLM every time, the prompt becomes too long, which increases API costs and slows down the response. 
  > 
  > To prevent this, I only pass the **last 4 to 5 messages** of the chat history to the LLM. In addition, when we scrape web pages, we limit the text to the first **10,000 characters** so we don't overload the context window."

---

## 🔍 2. RAG (Vector DB) & Multi-User Privacy

### Q4: How do you make sure User A cannot see or search User B's uploaded files in Pinecone?
* **Student Answer**: 
  > "Since we use a shared Pinecone vector database, security is a major priority. We solve this using **metadata tags**:
  > 
  > 1. When User A uploads a document, we break it into chunks and tag every chunk with `user_id = A` and the `file_name` in the metadata.
  > 2. When User A asks a question, we tell Pinecone to perform a similarity search *only* on chunks matching the filter `{"user_id": A}`.
  > 
  > This filters out everyone else's documents at the database level, ensuring complete privacy."

### Q5: What is text-chunking, and why did you choose your chunk size?
* **Student Answer**: 
  > "LLMs cannot read a whole 50-page PDF at once. We have to cut the document into smaller pieces called 'chunks'. 
  > 
  > I used a tool called `RecursiveCharacterTextSplitter` with a **chunk size of 1000 characters** and an **overlap of 200 characters**:
  > * A chunk size of 1000 is small enough for fast searches but large enough to contain complete paragraphs and context.
  > * The 200-character overlap acts like a buffer. It ensures that if a sentence gets cut in half between two chunks, the full meaning is preserved in both."

### Q6: What happens to the database when a user updates or deletes a file?
* **Student Answer**: 
  > "If a user deletes a file, we must remove its chunks from the vector database, or else the LLM will still use that old info to answer questions. 
  > 
  > In my code, when a file is deleted or updated, we run a query in Pinecone to **delete all vectors** matching that specific `user_id` and `file_name`. For updates, we delete the old chunks first, and then upload the newly embedded chunks."

---

## 📂 3. File Storage & Conversion

### Q7: Why did you use both local folder storage and AWS S3?
* **Student Answer**: 
  > "We use a **hybrid storage** approach to get the best of both worlds:
  > * **AWS S3** is our secure cloud backup. If our server restarts or crashes, S3 keeps the files safe.
  > * **Local Caching** saves a copy of the file on the server. Libraries like PyMuPDF need a local file path to parse text quickly. Checking the local folder first prevents us from downloading from S3 repeatedly, saving network bandwidth and time."

### Q8: How do you display or download files securely in the frontend?
* **Student Answer**: 
  > "We don't expose direct, public links to our AWS S3 bucket because anyone could access them. 
  > 
  > Instead, when a user wants to view a file, Django requests a **presigned URL** from AWS. This is a temporary link that contains a security signature and is valid for only **1 hour**. After 1 hour, the link expires and is useless, keeping the files secure."

### Q9: How do you write plain text into a PDF or Word document programmatically?
* **Student Answer**: 
  > "We use specific Python libraries:
  > * For **Word (.docx)** files: We use `python-docx` to create a new document object, append paragraphs line-by-line, and save the binary data.
  > * For **PDFs**: We use `fpdf2` to create a new page, set a font, write the text in a multi-line format, and generate the PDF binary.
  > * We also use these libraries in reverse (using `PyMuPDF` for PDFs) to extract text when the LLM needs to read them."

---

## 🌐 4. Web Search & Scraping

### Q10: Why did you use Jina Reader instead of standard scraping libraries?
* **Student Answer**: 
  > "If you scrape a website with standard libraries (like BeautifulSoup), you get a lot of clutter: navigation bars, ads, footer links, and CSS styles. This clutter wastes LLM tokens and confuses the AI.
  > 
  > **Jina Reader** (`r.jina.ai`) is an API that reads a URL, strips out all the junk, and returns only the clean, readable Markdown text. It saves us a lot of tokens and helps the LLM give much better answers."

### Q11: How does the system handle errors like rate limits or search failures?
* **Student Answer**: 
  > "We build safeguards into the code:
  > * **Search Failures**: If DuckDuckGo search fails or runs out of requests, the agent falls back to the LLM's general knowledge instead of throwing an error.
  > * **Rate Limits**: If the LLM rate limit is reached, our Django view catches the error and sends a friendly message ('Rate limit reached, try again in a few minutes') to the user instead of letting the app crash."

---

## 🔒 5. Security & System Design

### Q12: How do you prevent users from accessing files they don't own (e.g. typing `../../etc/passwd`)?
* **Student Answer**: 
  > "We prevent this using a **three-step safety check**. Think of it like a **gym locker room** with a helpful but strict receptionist:
  > 
  > 1. **Filename Stripping (Ignoring trick directions)**: If a user tries to type `../../etc/passwd` to sneak into the system files, we use `os.path.basename` to strip away everything except the final name (so it becomes just `passwd`). In our locker room analogy, if a member hands the receptionist a note saying: *'Go to Locker 5, then walk out the backdoor to the manager's cash register'*, the receptionist ignores the directions and says: *'I am only looking at the locker number, which is 5.'*
  > 2. **Folder Scoping (Restricting physical access)**: We hardcode the folder path as `settings.MEDIA_ROOT / "users" / str(user_id)`. The code is physically locked inside that folder. In our analogy, the receptionist is legally only allowed to walk inside the locker room floor. They physically cannot walk into the manager's office or other areas, no matter what.
  > 3. **Database Check (Verifying ownership)**: Before reading any file, we query our database to verify if that filename is registered to that specific `user_id`. In our analogy, before opening Locker 5, the receptionist checks the register: *'Is Locker 5 registered to your member card?'* If the database says no, the request is rejected immediately."

### Q13: If 10,000 users use this app at once, what will break and how would you fix it?
* **Student Answer**: 
  > "The main bottlenecks would be:
  > 1. **File Ingestion**: Uploading and chunking large PDFs takes a lot of CPU power and would freeze the server.
  > 2. **LLM Limits**: We would hit Groq API rate limits very quickly.
  > 
  > **How I would fix it**:
  > * Move the document chunking and indexing to a background queue system using **Celery** and **Redis** so the main server stays responsive.
  > * Use connection pooling (like **pgBouncer**) to handle database connections.
  > * Cache repeat search queries in Redis to avoid hitting the LLM API unnecessarily."
