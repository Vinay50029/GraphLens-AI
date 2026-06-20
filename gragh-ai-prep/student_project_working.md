# 🚀 GraphLens AI: How the Project Works (Student-Friendly Guide)

This guide explains the step-by-step working of **GraphLens AI** in a simple way that is perfect for explaining in interviews.

---

## 🔄 1. The High-Level Flow (What happens when a user types a message?)

If an interviewer asks: *"Walk me through the lifecycle of a user query in your system,"* here is how you answer:

1. **User inputs a prompt** in the Chat UI.
2. The query is received by the Django API endpoint `/api/chat`.
3. Django passes the conversation history to the **LangGraph Orchestrator**.
4. The **Supervisor Node** looks at the question and determines which specialist agent is needed:
   * If the user wants to manage files $\rightarrow$ **File Agent**.
   * If the user has a document selected and is asking about it $\rightarrow$ **Document Agent**.
   * If the user is asking about current events or general knowledge $\rightarrow$ **Web Researcher Agent**.
5. The chosen agent executes its task, gets the result, and returns it to the supervisor.
6. The supervisor compiles the final answer, and Django sends it back to the React/HTML frontend to show the user.

---

## 📂 2. Document Ingestion (How do documents get uploaded and stored?)

### Q1: What happens when a user uploads a PDF or Word document?
* **Student Answer**: 
  > "It goes through a 3-step pipeline:
  > 1. **Parsing**: When a file is uploaded, the Django backend uses `PyMuPDF` (for PDFs) or `python-docx` (for Word) to extract all the raw text from the document.
  > 2. **Chunking**: The extracted text is cut into smaller pieces (chunks of 1,000 characters) so the database can handle them easily.
  > 3. **Embedding & Upload**: We pass these text chunks to Pinecone's embedding model (`llama-text-embed-v2`) which converts the text into mathematical coordinates (vectors). We then upload these vectors to the **Pinecone Vector Database**, tagged with the user's ID."

### Q2: Why do we convert text to "embeddings" (vectors)?
* **Student Answer**: 
  > "Computers don't understand the meaning of words like humans do. **Embeddings** convert words and sentences into lists of numbers (vectors) representing their meaning.
  > 
  > If two sentences are about similar topics (like 'The sky is blue' and 'It is a sunny day'), their numbers will be very close to each other. This allows us to perform **semantic search**—finding matching content by meaning rather than just looking for exact keyword matches."

---

## 🔍 3. Document Retrieval & Q&A (RAG)

### Q3: How does the Document Q&A agent answer questions based on the uploaded file?
* **Student Answer**: 
  > "We use a technique called **RAG (Retrieval-Augmented Generation)**:
  > 1. When the user asks a question (e.g., *'What is the company's Q3 revenue?'*), we convert that question into an embedding (vector).
  > 2. We query the Pinecone database to find the top 4 chunks of the document that have the most similar vectors to the question.
  > 3. We retrieve the plain text of those 4 chunks and feed them to the **Groq LLM** alongside the user's question.
  > 4. We instruct the LLM: *'Answer this question using ONLY this provided context.'* This prevents the AI from guessing or making things up (hallucinating)."

---

## 🌐 4. Web Search and Deep-Scraping

### Q4: How does the Web Researcher Agent work when the user asks about current events?
* **Student Answer**: 
  > "If the user asks about something current (like *'What is today's stock price of Apple?'*), the document agent won't know the answer. 
  > 
  > The **Web Researcher Agent** handles this using a tool-use loop (ReAct agent):
  > 1. It uses a **DuckDuckGo Search tool** to query the live internet and get a list of relevant websites and summaries.
  > 2. If the user provides a specific link or the agent needs deeper details, it uses **Jina Reader** to scrape and convert that website into clean text.
  > 3. It feeds that fresh internet text to the LLM to write a grounded, up-to-date answer."

---

## 📂 5. The File Agent and Auto-Indexing Sync

### Q5: What happens when the user asks the File Agent to save the search results?
* **Student Answer**: 
  > "The user can say: *'Save this summary into a file named summary.txt'*. 
  > 1. The **File Agent** calls the `create_file` tool.
  > 2. The code writes the file locally inside the user's server folder and uploads a backup to **AWS S3**.
  > 3. **Auto-Indexing**: Immediately after the file is saved, the agent triggers the ingestion pipeline in the background. It chunks the new file and uploads its embeddings to Pinecone.
  > 
  > This means the user can instantly start asking questions about the new file they just created!"
