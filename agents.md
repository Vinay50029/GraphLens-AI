# 🤖 GraphLens-AI Agent Architecture

This document outlines the detailed logic, flow, and responsibilities of the four specialized agents in the multi-agent system.

---

## 1. 🧠 LangGraph Supervisor (`supervisor_node`)
The Supervisor acts as the traffic controller/router of the system. It runs first and decides which worker agent should handle the incoming user request.

* **File Location:** [supervisor.py](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/supervisor.py)
* **Node Implementation:** [supervisor_node](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/supervisor.py#L88)

### Flow & Logic:
1. **Deterministic File Check:** It checks the user query via [_looks_like_file_query](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/supervisor.py#L42). If keywords like `create`, `write`, `read`, `delete`, `list files`, `.txt`, `.docx`, or `.pdf` are present, it **immediately bypasses** the LLM and routes directly to the `file_agent`.
2. **Deterministic Document Preference:** If a file is selected as the `active_document` in the frontend UI, and the query does not look like a web/current-events query (checked via [_looks_like_web_query](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/supervisor.py#L21)), it routes directly to the `document_agent`.
3. **Structured LLM Classification:** If neither of the deterministic rules trigger, the Supervisor queries Groq (`llama-3.1-8b-instant` with `temperature=0.0` for reliability) using structured output constraint [RouteSchema](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/supervisor.py#L15). The LLM decides among `'document_agent'`, `'researcher_agent'`, or `'file_agent'` based on:
   * System descriptions of each worker.
   * User query.
   * Recent conversation history (up to the last 5 messages).
4. It sets the `next_agent` state key, which the graph [router](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/graph/workflow.py#L18) reads to branch the execution.

---

## 2. 📄 Document Agent (`document_node`)
The Document Agent is a Retrieval-Augmented Generation (RAG) specialist. It answers user questions using only facts present in local documents.

* **File Location:** [document_agent.py](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/document_agent.py)
* **Node Implementation:** [document_node](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/document_agent.py#L16)

### Flow & Logic:
1. **Extract Target File:** It scans the user's query for specific document files matching extension regex (e.g. `report.docx`).
2. **Determine Search Scope:**
   * If an explicit filename is in the query, it scopes retrievals to that file.
   * If not, but there is an `active_document` in the graph state, it queries that file.
   * If no specific file is found, it performs a broad global retriever search across all files belonging to that user.
3. **Pinecone Vectorstore Query:** It calls `get_retriever(user_id, scoped_file_name)` to pull relevant text chunks from the Pinecone vector database.
4. **Context Framing:** If chunks are found, it formats them into a single string (`Context`). If none exist, it constructs a fallback message alerting the user.
5. **Strict Generation:** It builds a prompt providing the context and the recent history, asking the LLM (`temperature=0.2` for strict alignment) to answer *only* based on the context. If the answer isn't in the context, it says it doesn't know.

---

## 3. 🔍 Web Researcher Agent (`researcher_node`)
The Researcher Agent steps in when the user seeks live facts, recent news, or general knowledge not contained in local documents.

* **File Location:** [researcher.py](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/researcher.py)
* **Node Implementation:** [researcher_node](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/researcher.py#L33)

### Flow & Logic:
1. **ReAct Paradigm:** The Researcher is structured as a ReAct (Reasoning + Action) agent loop using LangGraph's prebuilt `create_react_agent`.
2. **Available Tools:**
   * `DuckDuckGoSearchRun`: Search engine to query internet articles, news, and pages.
   * [scrape_website](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/researcher.py#L18): Custom tool that calls the Jina Reader API (`https://r.jina.ai/{url}`) to scrape raw web links and return clean markdown text (truncated at 10,000 characters).
3. **Execution Loop:** The agent will search DuckDuckGo, read short descriptions, decide which links to read further, scrape them using the Jina Reader, and compile information.
4. **Synthesis:** Once it gathers enough facts, it synthesizes a final response summarizing the findings.

---

## 4. 💾 Workspace File Agent (`file_node`)
The File Agent manages the user's physical workspace files and directory structure. It bridges local system interaction and RAG updates.

* **File Location:** [file_agent.py](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/file_agent.py)
* **Node Implementation:** [file_node](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/file_agent.py#L223)

### Flow & Logic:
1. **Interactive ReAct Agent:** It runs as an autonomous agent equipped with specific file tools.
2. **Context Resolution:** The helper [_get_user_and_filename](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/file_agent.py#L41) ensures that if the user says "read this file", the agent binds the operation to the currently selected `active_document` unless another filename is named explicitly.
3. **Tool Suite:**
   * [create_file](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/file_agent.py#L68): Writes text content to disk. If the file is a text or document file (`.txt`, `.pdf`, `.docx`), it automatically runs `ingest_documents(...)` to chunk, embed, and store it in Pinecone.
   * [read_file](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/file_agent.py#L95): Reads local workspace files. It automatically converts binary formats like PDFs and Word files (`.docx`/`.doc`) into plain text to present it to the agent/user.
   * [update_file](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/file_agent.py#L126): Appends to or overwrites an existing file and automatically triggers Pinecone re-ingestion so the vector search index stays up-to-date.
   * [delete_file](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/file_agent.py#L174): Deletes the local workspace file and immediately purges all matching vector chunks from Pinecone.
   * [list_files](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/file_agent.py#L197): Lists all files in the user's storage directory.
4. **Outcome Delivery:** It completes the execution, returns a confirmation message explaining the file changes, and completes the graph run.
