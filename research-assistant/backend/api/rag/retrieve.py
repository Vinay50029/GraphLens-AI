import os
from typing import Optional
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "research-assistant")
EMBEDDING_MODEL = "llama-text-embed-v2"  # Matches your index configuration


def get_vectorstore():
    """
    Initializes and returns a PineconeVectorStore using Integrated Embeddings.
    """
    if not PINECONE_API_KEY:
        print("PINECONE_API_KEY not set — vectorstore unavailable.")
        return None

    try:
        embeddings = PineconeEmbeddings(model=EMBEDDING_MODEL, pinecone_api_key=PINECONE_API_KEY)
        return PineconeVectorStore(
            index_name=PINECONE_INDEX_NAME,
            embedding=embeddings,
            pinecone_api_key=PINECONE_API_KEY,
        )
    except Exception as e:
        print(f"Failed to initialize Pinecone vectorstore: {e}")
        return None


def get_retriever(file_name: Optional[str] = None):
    """
    Initializes and returns a Pinecone retriever using Integrated Embeddings.
    """
    vectorstore = get_vectorstore()
    if not vectorstore:
        return None

    try:
        search_kwargs = {"k": 6}
        if file_name:
            search_kwargs["filter"] = {"file_name": {"$eq": file_name}}

        return vectorstore.as_retriever(search_type="mmr", search_kwargs=search_kwargs)
    except Exception as e:
        print(f"Failed to initialize Pinecone retriever: {e}")
        return None
