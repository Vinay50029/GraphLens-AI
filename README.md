# 🚀 GraphLens AI

**GraphLens AI** is an AI-powered research workspace. It integrates document-based vector search (RAG), real-time web search, and an autonomous file management assistant into a secure, user-isolated chat platform.

---

## 📸 Demo / Preview

<img width="1498" height="897" alt="image" src="https://github.com/user-attachments/assets/fdbe63ad-414a-4d42-9f7c-ff89669ab2d9" />

---

## 🔄 System Flow

1. **Ingestion**: The user uploads a PDF, Word, or Text document. The Django backend parses and extracts text using PyMuPDF or python-docx.
2. **Indexing**: Extracted content is chunked, embedded, and indexed into **Pinecone Serverless**, tagged with the user's specific ID to ensure multi-tenant isolation.
3. **User Query**: The user sends a prompt through the chat interface.
4. **Supervisory Routing**: The **LangGraph Supervisor** inspects the query to check if it's a file operation (e.g. creating/reading files), or dynamically routes it to the correct worker agent.
5. **Agent Execution**:
   * *Document Agent*: Performs a similarity search in Pinecone scoped to the user's active document.
   * *Research Agent*: Conducts a live internet search on DuckDuckGo and deep-scrapes URLs using Jina Reader.
   * *Workspace File Agent*: Creates, reads, updates, or deletes files directly inside the user's directory on the server.
6. **Synthesis & Sync**: The consolidated context is passed to the Groq LLM to generate a grounded response. Any files created or modified by the File Agent are automatically re-indexed back into Pinecone.

---

## 🚀 Key Features

### 🧠 Intelligent Agent Routing (LangGraph)
* **Built using LangGraph Supervisor Architecture**.
* **Intent-Based Logic**: Decides whether a query requires document Q&A, a live web search, or workspace file operations.

### 🔍 Isolated Document RAG
* **Multi-Tenant Privacy**: Scopes document ingestion and vector database retrieval by user session to keep files completely private.
* **Semantic Vector Search**: Powered by Pinecone to query text chunks using cosine similarity.

### 🌐 Real-Time Web Research
* **Live Search**: Fetches real-time internet facts using the DuckDuckGo Search API.
* **URL Deep-Scraping**: Converts links into clean markdown content via the Jina Reader API for the LLM to analyze.

### 📂 Chat-Based File Manager
* **Workspace CRUD**: Allows users to manage server files (create, read, append, overwrite, delete) directly through chat instructions.
* **Auto-Sync Indexing**: Automatically indexes file edits and creations in the background database.

---

## 🎯 Use Cases
* **📚 Academic Research**: Ask questions about reference PDFs and instantly verify claims on the live web.
* **📄 Workspace Note-Taking**: Summarize documents or web research and save the results as new files in your workspace.
* **🔒 Isolated Data Auditing**: Securely compare local records against current web search results.

---

## 🛠️ Tech Stack
* **Frontend**: Vanilla HTML5, CSS3, and JavaScript (served directly via Django templates).
* **Backend**: Django & Django REST Framework (DRF).
* **AI Orchestration**: LangChain & LangGraph.
* **AI Engine**: Groq Cloud API (`llama-3.1-8b-instant`).
* **Vector Database**: Pinecone Serverless (with `llama-text-embed-v2` embeddings).
* **Relational Database**: Neon PostgreSQL (production) or SQLite (local development).
* **Cloud Storage**: AWS S3 (integrated via `boto3` using presigned URLs).

---

## 🚀 Future Roadmap
- [ ] 🔹 **Google Workspace Integration** (Docs, Drive, Gmail)
- [ ] 🔹 **Multi-File Chat**: Simultaneous querying across multiple documents.
- [ ] 🔹 **Persistent Memory**: Longer-term session history for returning users.
- [ ] 🔹 **Enterprise Auth**: Production-grade user authentication systems.

---

## 📬 Contact
📧 **vinaygattu005@gmail.com**  
🔗 **GitHub**: [Vinay50029](https://github.com/Vinay50029)  

---
⭐ **If you like this project, give it a star on GitHub — it helps a lot!**
