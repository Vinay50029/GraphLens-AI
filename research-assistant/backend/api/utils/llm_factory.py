import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_llm(temperature: float = 0.0):
    """
    Returns a ChatGroq LLM instance.
    Uses GROQ_API_KEY from the .env file.
    Model: llama3-70b-8192 (free-tier Groq model)
    """
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in your .env file!")
    
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        api_key=groq_api_key,
    )
