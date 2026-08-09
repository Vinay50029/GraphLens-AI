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


def get_retriever(user_id: int, file_names = None):
    """
    Initializes and returns a Pinecone retriever using Integrated Embeddings.
    Can filter by a single file name (string or list of 1 element),
    or a list of file names (if file_names is a list/tuple).
    """
    vectorstore = get_vectorstore()
    if not vectorstore:
        return None

    try:
        search_kwargs = {"k": 10}
        
        # Enforce user separation metadata filter
        filters = {"user_id": {"$eq": user_id}}
        if file_names:
            if isinstance(file_names, str):
                filters["file_name"] = {"$eq": file_names.strip()}
            elif isinstance(file_names, (list, tuple)):
                cleaned_names = [f.strip() for f in file_names if f.strip()]
                if len(cleaned_names) == 1:
                    filters["file_name"] = {"$eq": cleaned_names[0]}
                elif len(cleaned_names) > 1:
                    filters["file_name"] = {"$in": cleaned_names}
            
        search_kwargs["filter"] = filters

        return vectorstore.as_retriever(search_type="mmr", search_kwargs=search_kwargs)
    except Exception as e:
        print(f"Failed to initialize Pinecone retriever: {e}")
        return None
