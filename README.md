---
title: Intelligent Research Assistant
emoji: 🦀
colorFrom: blue
colorTo: pink
sdk: streamlit
sdk_version: 1.39.0
app_file: app.py
pinned: false
---

# Intelligent Research Assistant

A multi-agent application that combines PDF RAG (Retrieval Augmented Generation) with live web search to help with research tasks.

## Tech Stack
- **Framework**: LangChain, LangGraph
- **Database**: ChromaDB
- **Frontend**: Streamlit
- **Model**: OpenAI GPT-4o
- **Search**: Tavily

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Add API keys to `.env`.
3. Run the app:
   ```bash
   streamlit run app.py
   ```
