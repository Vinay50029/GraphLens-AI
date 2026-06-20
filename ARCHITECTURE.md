# 🏗️ GraphLens AI Architecture & Flow

This document details the multi-agent orchestration, key components, libraries, and system flow design of the **GraphLens AI** workspace.

---

## 🔄 System Flow Chart

```mermaid
graph TD
    User([User]) -->|1. Upload Doc / Ask Question| DRF[Django REST API /api/chat & /api/ingest]
    
    %% Ingestion Flow
    DRF -->|Ingest PDF/Docx/Txt| Ingest[Ingestion Pipeline]
    Ingest -->|Parse Text & PyMuPDF| Chunk[Recursive Text Chunking]
    Chunk -->|Embed: llama-text-embed-v2| Pinecone[(Pinecone Vector DB)]
    
    %% Orchestration Flow
    DRF -->|Trigger Chat| Graph[LangGraph Orchestration]
    Graph -->|Initialize GraphState| Supervisor{Supervisor Node}
    
    %% Routing Logic
    Supervisor -->|Check 1: Workspace/File Keywords?| FileAgent[Workspace File Agent]
    Supervisor -->|Check 2: Active Doc & No Web Keywords?| DocAgent[Document Agent]
    Supervisor -->|Check 3: Structured LLM Classification| RouterLLM[Router LLM Decision]
    
    RouterLLM -->|Route to Document| DocAgent
    RouterLLM -->|Route to Researcher| ResearcherAgent[Web Researcher Agent]
    RouterLLM -->|Route to File| FileAgent
    
    %% Agent Execution Details
    DocAgent -->|Query Vectorstore by User Scope| Pinecone
    DocAgent -->|Context + Prompt| LLM_Doc[Groq Llama-3.1-8b-instant]
    
    ResearcherAgent -->|Search Query| DDG[DuckDuckGo Search Tool]
    ResearcherAgent -->|Link URL| Scrape[Jina Reader Scrape Tool]
    
    FileAgent -->|File Operations| OS[Local User Workspace]
    FileAgent -->|Auto-sync updates| Pinecone
    
    %% Synthesis & Response
    LLM_Doc -->|Synthesized Answer| Response[Final AI Answer]
    DDG & Scrape -->|Live Web Context| LLM_Web[Groq LLM] -->|Synthesized Answer| Response
    OS -->|File Action Feedback| Response
    
    Response -->|Return Response| DRF
    DRF -->|Render in Chat UI| User

    classDef main fill:#5271FF,stroke:#fff,stroke-width:2px,color:#fff;
    classDef agent fill:#00C9A7,stroke:#fff,stroke-width:2px,color:#fff;
    classDef database fill:#FF8066,stroke:#fff,stroke-width:2px,color:#fff;
    classDef tool fill:#845EC2,stroke:#fff,stroke-width:2px,color:#fff;
    
    class User,DRF,Response main;
    class Supervisor,FileAgent,DocAgent,ResearcherAgent agent;
    class Pinecone database;
    class Ingest,DDG,Scrape,OS tool;
```

---

## 🧠 Multi-Agent Orchestration

The backend uses **LangGraph** to build a state machine containing a team of specialized agents:

1. **LangGraph Supervisor**: Inspects incoming queries. If the query asks for workspace file operations (e.g. creating/reading files), it routes to the **File Agent**. If the user is viewing a document, it defaults to the **Document Agent**. Otherwise, an LLM classifier selects the best worker.
2. **Document Agent**: Similarity-searches the vectorstore for user-scoped content and constructs grounded answers.
3. **Web Researcher Agent**: Performs DuckDuckGo searches and deep-scrapes specific links via Jina Reader (`https://r.jina.ai/`).
4. **Workspace File Agent**: Creates, reads, appends to, or deletes files in the user directory, automatically syncing edits back into Pinecone database chunks.

---

## 🛠️ Technology Stack & Dependencies

* **Frontend**: HTML5, Vanilla JS & CSS (Custom dark theme with glassmorphism).
* **Backend**: Django & Django REST Framework (DRF).
* **AI Orchestration**: LangChain & LangGraph (agent flow state machine).
* **LLMs**: Groq Chat Engine (`llama-3.1-8b-instant` for reasoning and routing).
* **Vector Database**: Pinecone Serverless (utilizes `llama-text-embed-v2` embeddings for chunk-level semantic searches).
* **Relational Database**: Neon PostgreSQL (connected via `dj-database-url` and `psycopg2-binary` to store user registration, login credentials, and file metadata).
* **Cloud Storage**: AWS S3 (integrated via `boto3` to store, download, and serve original uploaded files using secure 1-hour presigned URLs).
