# GraphLens AI

**GraphLens AI** is an advanced, autonomous research engine that combines graph-based reasoning with multi-modal vision capabilities. It bridges the gap between your personal workspace (Google Drive, Gmail) and state-of-the-art Large Language Models.

## Features
- **Graph-Based Reasoning**: Powered by LangGraph for complex, multi-step agent workflows.
- **Vision & OCR**: Intelligent document understanding using Gemini and custom OCR vision pipelines.
- **Workspace Integration**: Seamlessly search and retrieve information from Google Drive and Gmail.
- **RAG Architecture**: High-performance retrieval using Pinecone v6 and Integrated Embeddings.
- **Modern UI**: Sleek React frontend with a robust Django REST backend.

## Tech Stack
- **Frontend**: React, Vite, Vanilla CSS
- **Backend**: Django, Django REST Framework
- **LLM/AI**: Groq (Llama 3), Google Gemini 1.5 Flash
- **Orchestration**: LangChain, LangGraph
- **Vector Database**: Pinecone
- **Utilities**: Vision OCR, Google API Integration

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js & npm
- API Keys: Groq, Google AI (Gemini), Pinecone, Google Workspace JSON.

### Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/Vinay50029/GraphLens-AI.git
   cd GraphLens-AI
   ```

2. **Backend Setup:**
   ```bash
   cd research-assistant/backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

3. **Frontend Setup:**
   ```bash
   cd research-assistant/frontend
   npm install
   npm run dev
   ```

## License
MIT License
