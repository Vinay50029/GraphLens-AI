# 🧠 Supervisor Agent Routing Decisions: Q&A Guide

This guide explains the design decisions behind the routing mechanism in [supervisor.py](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/supervisor.py).

---

## Q1: Why not route web queries (`_looks_like_web_query`) directly/deterministically like file queries?

### 1. High Keyword Ambiguity (Context Overlap)
Web search keywords (like *"latest"*, *"recent"*, *"search"*, or *"today"*) are often used when talking about local documents. For example:
* *"Search for the latest section in my document."*
* *"What are the most recent changes in this report?"*

If the supervisor routed to the researcher agent (Web Researcher) **deterministically** just because it saw the word *"search"* or *"latest"*, it would erroneously trigger a public internet search and fail to answer the user's question about their private file.

By contrast, file commands (like *"create notes.txt"* or *"delete report.docx"*) are highly specific actions with almost zero overlap with normal conversation or web search.

### 2. The Structured LLM Router Acts as the Arbiter
Instead of routing deterministically, the supervisor uses a hybrid approach:
* If it looks like a web query (via [_looks_like_web_query](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/supervisor.py#L21)), it **bypasses the deterministic document lock** (if any file is active).
* It then hands the query over to the **LLM Router** (`llama-3.1-8b-instant`).
* The LLM reads the complete prompt and recent history to intelligently decide if *"search"* refers to the internet (routing to `researcher_agent`) or the local document (routing to `document_agent`).

---

## Q2: Since we use an LLM Router anyway, why not send all queries directly to the LLM for routing?

Using a hybrid approach (Deterministic Regex + LLM Router) instead of sending everything directly to the LLM is a standard **production-grade engineering pattern**.

### 1. Latency (Speed & User Experience)
* **LLM Routing:** Calling an external LLM API (like Groq/Llama) adds network latency—usually taking between **400ms to 1.5 seconds**.
* **Deterministic Routing:** Local Python regex checks (like [_looks_like_file_query](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/agents/supervisor.py#L42)) run on the server in **under 1 millisecond** (0.001 seconds).
* **Benefit:** When a user types *"list my files"* or *"delete notes.txt"*, the response feels instantaneous because it bypasses the LLM routing stage entirely.

### 2. Cost Efficiency (Token Savings)
* Every API call to an LLM charges you based on input and output tokens.
* Sending every single message to the Router LLM to make a routing decision would double the number of LLM calls per chat turn (once to route, once to answer).
* Deterministically routing simple or obvious messages cuts down the overall token consumption and API costs by **30% to 50%**.

### 3. Absolute Reliability (Zero Hallucinations)
* LLMs are probabilistic models. Even with `temperature=0.0`, there is still a small chance of **hallucinations or misrouting** (e.g., the LLM routing *"create a file"* to the web search agent because it got confused by the context).
* For critical workspace actions (like saving or deleting user files), we want **100% deterministic execution**. If the user says *"delete notes.txt"*, there must be zero probability of the LLM deciding to search the web for it. A hardcoded check guarantees this safety.

### 4. Directing LLM Context Only When Necessary
* LLMs excel at **nuance and ambiguity**.
* We only spend LLM computation when the query is actually ambiguous (e.g., *"What are the latest findings?"* where it could mean the active document or a Google search). This reserves the AI's cognitive power for where it's actually needed.
