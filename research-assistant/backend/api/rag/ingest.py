import os
from typing import Optional
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "research-assistant")


def ingest_documents(pdf_path: str, user_id: int, original_file_name: Optional[str] = None) -> dict:
    """Loads a document (Text, Word, or PDF), splits it, and uploads to Vector Store."""
    vector_db_type = os.environ.get("VECTOR_DB_TYPE", "pinecone").lower()

    if vector_db_type == "pinecone" and not PINECONE_API_KEY:
        return {"success": False, "message": "PINECONE_API_KEY is not set."}

    try:
        file_name = (original_file_name or os.path.basename(pdf_path)).strip()
        
        # Purge existing chunks for this user and file to avoid duplicate/stale vectors
        delete_document_index(user_id, file_name)
        
        ext = file_name.lower().split('.')[-1]

        # 1. Load document text
        if ext == "txt":
            with open(pdf_path, 'r', encoding='utf-8', errors='ignore') as f:
                docs = [Document(page_content=f.read())]
        elif ext == "pdf":
            docs = PyMuPDFLoader(pdf_path).load()
        else:
            return {"success": False, "message": "Unsupported file format. Only PDF and TXT are supported."}

        # 2. Add metadata (so each chunk knows its source file and user ownership)
        for doc in docs:
            doc.metadata.update({"file_name": file_name, "user_id": user_id})

        # 3. Split the text into smaller chunks
        splits = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)

        # 4. Upload chunks to Vector DB
        from api.rag.retrieve import get_embeddings
        embeddings = get_embeddings()

        if vector_db_type == "chroma":
            from langchain_community.vectorstores import Chroma
            db_dir = os.environ.get("CHROMA_DB_DIR", "db/chroma_db")
            Chroma.from_documents(splits, embeddings, persist_directory=db_dir)
        else:
            # Create Pinecone Index if it does not exist
            from pinecone import Pinecone, ServerlessSpec
            from langchain_pinecone import PineconeVectorStore
            pc = Pinecone(api_key=PINECONE_API_KEY)
            if PINECONE_INDEX_NAME not in [idx.name for idx in pc.list_indexes()]:
                pc.create_index(
                    name=PINECONE_INDEX_NAME,
                    dimension=1024,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
            PineconeVectorStore.from_documents(splits, embeddings, index_name=PINECONE_INDEX_NAME)

        return {"success": True, "message": f"Successfully ingested {len(splits)} chunks.", "chunks": len(splits)}

    except Exception as e:
        return {"success": False, "message": f"Ingestion failed: {str(e)}"}


def delete_document_index(user_id: int, file_name: str) -> bool:
    """Deletes all chunks for a specific file and user from the active vector store."""
    vector_db_type = os.environ.get("VECTOR_DB_TYPE", "pinecone").lower()

    if vector_db_type == "chroma":
        try:
            from langchain_community.vectorstores import Chroma
            from api.rag.retrieve import get_embeddings
            db_dir = os.environ.get("CHROMA_DB_DIR", "db/chroma_db")
            embeddings = get_embeddings()
            vectorstore = Chroma(persist_directory=db_dir, embedding_function=embeddings)
            results = vectorstore.get(where={"$and": [{"user_id": user_id}, {"file_name": file_name.strip()}]})
            if results and results["ids"]:
                vectorstore.delete(ids=results["ids"])
            return True
        except Exception as e:
            print(f"Failed to delete local Chroma index for {file_name}: {e}")
            return False
    else:
        if not PINECONE_API_KEY:
            return False
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=PINECONE_API_KEY)
            index = pc.Index(PINECONE_INDEX_NAME)
            index.delete(filter={"user_id": user_id, "file_name": file_name.strip()})
            return True
        except Exception as e:
            print(f"Failed to delete Pinecone index for {file_name}: {e}")
            return False
