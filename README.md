# 🚀 GraphLens AI: Intelligent Research Assistant

**GraphLens AI** is a professional-grade, multi-agent AI research platform that enables users to query both private documents (PDFs) and the live web in a single interface. It bridges the gap between static document analysis and real-time information retrieval.

---

## 📸 Demo / Preview

<img width="1493" height="883" alt="image" src="https://github.com/user-attachments/assets/ec2e33bc-61c5-4a6d-8ee0-6f4e7bedcd2e" />

## 🔄 System Flow

1.  **Ingestion**: User uploads a PDF. The backend extracts text or uses **Vision-OCR** for scanned docs.
2.  **Indexing**: Content is chunked and embedded into **Pinecone** with file-specific metadata.
3.  **User Query**: The user asks a question in the **React** interface.
4.  **Supervision**: The **LangGraph Supervisor** analyzes the query intent.
5.  **Agency Execution**: 
    *   *Route A*: **Document Agent** performs a similarity search in Pinecone.
    *   *Route B*: **Research Agent** performs a live web search or deep-scrape.
6.  **Synthesis**: The context is consolidated and passed to **Groq LLM** for a grounded, accurate response.
7.  **Final Delivery**: The answer is returned to the frontend for a seamless user experience.

---

## 🚀 Key Features

### 🧠 Intelligent Agent Routing (LangGraph)
*   **Built using LangGraph Supervisor Architecture**.
*   **Autonomous Logic**: Decides whether a query requires internal **Document Research** (Pinecone) or **Live Web Research** (DuckDuckGo Search).

### 🔍 Advanced RAG Pipeline
*   **Semantic Chunking**: Intelligent text splitting for better context preservation.
*   **Pinecone (Serverless)**: High-speed vector search for large document sets.
*   **MMR (Maximum Marginal Relevance)**: Ensures diverse retrieval results without duplication.

### 🖼️ Multimodal OCR (Vision AI)
*   **Vision-Integrated Fallback**: Powered by **Groq Llama 3.2 Vision**.
*   **Image Ingestion**: Automatically detects scanned/image-based PDFs, renders pages, and extracts high-accuracy text, tables, and chart descriptions.

### 🌐 Real-Time Web Research Agent
*   **Live Web Browsing**: Real-time information retrieval using the DuckDuckGo API.
*   **Deep Scraper**: Extracts full-page content from URLs using BeautifulSoup.
*   **Structured Scraping**: Includes custom logic for specialized sites (e.g., LeetCode profile analytics via GraphQL).

---

## 🎯 Use Cases
*   **📚 Research Paper Analysis**: Instantly summarize and query complex academic findings.
*   **📄 Resume / Career Insights**: Deep-dive into professional documents for key milestones.
*   **🧠 AI-Powered Study Assistant**: Bridge textbook knowledge with the latest web developments.
*   **🌐 Real-Time Data Analysis**: Get information beyond the traditional LLM knowledge cutoff.

---

## 🛠️ Tech Stack
*   **Frontend**: React (Vite) + Vanilla CSS (Modern Design)
*   **Backend**: Django & Django REST Framework (DRF)
*   **Orchestration**: LangChain & LangGraph
*   **AI Engine**: Groq (Llama-3, Vision-3.2), Gemini
*   **Database**: Pinecone (Vector Database)
*   **Deployment**: Vercel (Frontend) & Render (Backend)

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
