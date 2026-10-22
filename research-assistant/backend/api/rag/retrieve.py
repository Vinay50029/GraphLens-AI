import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

def get_embeddings():
    """
    Returns the appropriate embeddings model.
    """
    vector_db_type = os.environ.get("VECTOR_DB_TYPE", "pinecone").lower()
    if vector_db_type == "chroma":
        from langchain_huggingface import HuggingFaceEmbeddings
        model_name = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        return HuggingFaceEmbeddings(model_name=model_name)
    else:
        from langchain_pinecone import PineconeEmbeddings
        pinecone_api_key = os.environ.get("PINECONE_API_KEY")
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is not set.")
        model_name = os.environ.get("EMBEDDING_MODEL", "llama-text-embed-v2")
        return PineconeEmbeddings(model=model_name, pinecone_api_key=pinecone_api_key)


def get_vectorstore():
    """
    Initializes and returns the active VectorStore (Chroma or Pinecone).
    """
    vector_db_type = os.environ.get("VECTOR_DB_TYPE", "pinecone").lower()

    try:
        embeddings = get_embeddings()
        if vector_db_type == "chroma":
            from langchain_community.vectorstores import Chroma
            db_dir = os.environ.get("CHROMA_DB_DIR", "db/chroma_db")
            return Chroma(persist_directory=db_dir, embedding_function=embeddings)
        else:
            from langchain_pinecone import PineconeVectorStore
            pinecone_index_name = os.environ.get("PINECONE_INDEX_NAME", "research-assistant")
            pinecone_api_key = os.environ.get("PINECONE_API_KEY")
            return PineconeVectorStore(
                index_name=pinecone_index_name,
                embedding=embeddings,
                pinecone_api_key=pinecone_api_key,
            )
    except Exception as e:
        print(f"Failed to initialize vectorstore ({vector_db_type}): {e}")
        return None


def get_retriever(user_id: int, file_names = None):
    """
    Initializes and returns a retriever using the configured VectorStore.
    Filters queries by user_id and optionally file name(s).
    """
    vectorstore = get_vectorstore()
    if not vectorstore:
        return None

    try:
        search_kwargs = {"k": 10}
        vector_db_type = os.environ.get("VECTOR_DB_TYPE", "pinecone").lower()
        
        # Enforce user separation metadata filter
        if vector_db_type == "chroma":
            filters = {"user_id": user_id}
            if file_names:
                if isinstance(file_names, str):
                    filters = {
                        "$and": [
                            {"user_id": user_id},
                            {"file_name": file_names.strip()}
                        ]
                    }
                elif isinstance(file_names, (list, tuple)):
                    cleaned_names = [f.strip() for f in file_names if f.strip()]
                    if len(cleaned_names) == 1:
                        filters = {
                            "$and": [
                                {"user_id": user_id},
                                {"file_name": cleaned_names[0]}
                            ]
                        }
                    elif len(cleaned_names) > 1:
                        filters = {
                            "$and": [
                                {"user_id": user_id},
                                {"file_name": {"$in": cleaned_names}}
                            ]
                        }
        else:
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
        print(f"Failed to initialize retriever: {e}")
        return None
