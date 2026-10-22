import os
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

def get_llm(temperature: float = 0.0):
    """
    Returns an LLM instance.
    If USE_LOCAL_LLM=True, returns a ChatOllama instance pointing to local Ollama.
    Otherwise, returns a ChatGroq instance using GROQ_API_KEY from the .env file.
    """
    use_local = os.environ.get("USE_LOCAL_LLM", "False").lower() in ("true", "1", "yes")
    
    if use_local:
        local_model = os.environ.get("LOCAL_LLM_MODEL", "llama3.1")
        local_url = os.environ.get("LOCAL_LLM_URL", "http://localhost:11434")
        return ChatOllama(
            model=local_model,
            temperature=temperature,
            base_url=local_url,
        )
        
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in your .env file!")
    
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        api_key=groq_api_key,
    )
