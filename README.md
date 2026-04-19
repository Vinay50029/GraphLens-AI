# GraphLens AI

**GraphLens AI** is a high-performance, autonomous research engine built on a **Graph-based Multi-Agent architecture**. It combines document intelligence with real-time web research to provide comprehensive answers from both your uploaded files and the live internet.

## Features
- **Graph-Based Orchestration**: Powered by **LangGraph**, the system uses a Supervisor Agent to intelligently route tasks between a Document Research Agent and a Web Research Agent.
- **Multimodal Document Intelligence**: Features a specialized vision pipeline using **Groq (Llama 3.2 Vision)** to handle scanned PDFs and images via automated OCR fallback.
- **Agentic Web Research**: An autonomous web agent capable of searching the live internet (DuckDuckGo), scraping deep content from URLs, and even extracting specific data like LeetCode profiles.
- **High-Performance RAG**: Uses **Pinecone** with integrated **Llama-based embeddings** for fast and accurate context retrieval from large document sets.
- **Modern Full-Stack Architecture**: A sleek, responsive **React** frontend paired with a robust **Django REST** backend.

## Tech Stack
- **Orchestration**: LangChain & LangGraph
- **LLM Engine**: Groq (Llama 3.x for reasoning, Llama 3.2 Vision for OCR)
- **Vector Database**: Pinecone (Serverless)
- **Search Engine**: DuckDuckGo
- **Backend**: Django & Django REST Framework
- **Frontend**: React (Vite)
- **Utilities**: PyMuPDF, BeautifulSoup (Scraping)

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js & npm
- API Keys: **Groq** and **Pinecone**

