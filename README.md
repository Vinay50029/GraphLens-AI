# 🚀 GraphLens AI

**GraphLens AI** is an AI-powered research workspace. It integrates document-based vector search (RAG), real-time web search, and an autonomous file management assistant into a secure, user-isolated chat platform.

---

## 📸 Demo / Preview

<img width="1491" height="920" alt="image" src="https://github.com/user-attachments/assets/14604513-7de6-43f7-a23f-069fcbdfd695" />

---

## 🏗️ Interactive System Architecture

> 🚀 **[Click here to open the Live Interactive Architecture Diagram](https://vinay50029.github.io/GraphLens-AI/architecture.html)**  

<p align="center">
  <a href="https://vinay50029.github.io/GraphLens-AI/architecture.html">
    <img width="1620" height="799" alt="Architecture_Preview_flow" src="https://github.com/user-attachments/assets/9dad6ab9-d435-453c-9f5f-74252e5725f0" />
  </a>
</p>

---

## 🔄 System Flow

1. **Ingestion & Storage**: The user uploads a PDF or text document. The Django backend parses text using PyMuPDF, persists the file to **AWS S3** or local storage, and logs the metadata in the relational database (`UserFile`).
2. **Vector Indexing**: Extracted content is chunked and embedded using **all-MiniLM-L6-v2** or **llama-text-embed-v2**, then indexed into **Pinecone Serverless** or local **ChromaDB**, tagged with the user's `user_id` for multi-tenant isolation.
3. **User Query**: The user sends a prompt through the chat interface, optionally targeting active documents.
4. **Supervisory Routing**: The **LangGraph Supervisor** inspects the query using fast deterministic checks and structured LLM routing to delegate tasks across 4 specialized worker agents.
5. **Agent Execution**:
   * 📄 **Document RAG Agent**: Performs similarity searches across the vector database (Pinecone/ChromaDB) scoped to the user's active document and retrieves top context chunks.
   * 🔍 **Web Researcher Agent**: Conducts live internet searches on DuckDuckGo and deep-scrapes markdown text using Jina Reader (`r.jina.ai`) in an autonomous ReAct loop.
   * 📁 **Workspace File Agent**: Creates, reads, updates, or deletes files directly inside the user's workspace on disk/S3, automatically triggering vector store re-indexing.
   * 📧 **Email Agent**: Extracts recipient and document parameters, resolves attachments from storage/UserFile database, and dispatches emails via SMTP relay with custom `Reply-To` headers.
6. **Synthesis & Response**: Context is synthesized by the LLM (**Groq Cloud Llama-3.3-70B** or **Local Ollama Llama-3.1**) into a grounded answer, returned via Django REST Framework, and rendered live in the chat dashboard.

---

## 🚀 Key Features

## 🧠 Intelligent Agent Routing (LangGraph)
* **Built using LangGraph Supervisor Architecture**.
* **Intent-Based Dynamic Routing**: Automatically delegates queries between document RAG, web search, file management, and email dispatch.
### 🔍 Isolated Document RAG (Dual Vector Store)
* **Multi-Tenant Privacy**: Scopes document ingestion and vector retrieval by user session to ensure complete data isolation.
* **Flexible Vector Backend**: Seamlessly toggle between **Pinecone Serverless** (cloud) and **ChromaDB** (local disk).
* **Semantic Embeddings**: Powered by HuggingFace `all-MiniLM-L6-v2` or Pinecone `llama-text-embed-v2`.
### 🌐 Real-Time Web Research
* **Live Search**: Fetches real-time internet facts using DuckDuckGo.
* **URL Deep-Scraping**: Converts web pages into clean markdown via the Jina Reader API for the LLM to inspect.
### 📁 Chat-Based File Manager & Auto-Sync
* **Workspace CRUD**: Manage server and cloud files (create, read, append, overwrite, delete) directly through chat instructions.
* **Auto-Sync Indexing**: Background workers automatically re-embed and index modified files so vector search stays current.
### 📧 Automated Email Dispatch Agent
* **Attachment Delivery**: Sends workspace documents, PDFs, and generated reports directly to any recipient email.
* **Sender Identity**: Dispatches via central SMTP relay while attaching user identification and setting `Reply-To` headers.
### 💻 Hybrid AI Engine (Cloud + Local Offline)
* **Groq Cloud Engine**: High-speed inference using `llama-3.3-70b-versatile`.
* **Local Offline Engine**: 100% private, local inference using **Ollama** (`llama3.1`).

---

## 🎯 Use Cases
* **📚 Academic & Enterprise Research**: Ask questions about reference PDFs and verify claims with live web searches.
* **📄 Workspace Note-Taking & Drafting**: Summarize documents, draft reports, and save them directly as workspace files.
* **✉️ Direct Document Sharing**: Tell the agent to "send the summary report to colleague@example.com" and have it dispatched with attachment.
* **🔒 Privacy-First Offline Analysis**: Switch to Ollama + ChromaDB to run the entire RAG pipeline completely offline.

---

## 🛠️ Tech Stack
* **Frontend**: Vanilla HTML5, CSS3 (Glassmorphism theme), and JavaScript.
* **Backend**: Django & Django REST Framework (DRF).
* **AI Orchestration**: LangChain & LangGraph (Supervisor multi-agent state graph).
* **AI Inference (Hybrid)**:
  * **Cloud**: Groq Cloud API (`llama-3.3-70b-versatile`).
  * **Local / Offline**: Ollama (`llama3.1`).
* **Embeddings**: HuggingFace (`all-MiniLM-L6-v2`) & Pinecone Embeddings (`llama-text-embed-v2`).
* **Vector Databases**: Pinecone Serverless (cloud) & ChromaDB (local persistent).
* **Relational Database**: PostgreSQL / SQLite (Django ORM with `UserFile` & auth models).
* **Storage Vault**: AWS S3 (via `boto3` presigned URLs) & local user media cache.
* **Email & External APIs**: SMTP Mail Relay, DuckDuckGo Search, and Jina Reader API.

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
