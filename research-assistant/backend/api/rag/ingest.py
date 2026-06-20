import os
from typing import Optional
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from langchain_core.documents import Document

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "research-assistant")


def ingest_documents(pdf_path: str, user_id: int, original_file_name: Optional[str] = None) -> dict:
    """Loads a document (Text, Word, or PDF), splits it, and uploads to Pinecone."""
    if not PINECONE_API_KEY:
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

        # 4. Create Pinecone Index if it does not exist
        pc = Pinecone(api_key=PINECONE_API_KEY)
        if PINECONE_INDEX_NAME not in [idx.name for idx in pc.list_indexes()]:
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=1024,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        # 5. Upload chunks to Pinecone Vector DB
        embeddings = PineconeEmbeddings(model="llama-text-embed-v2", pinecone_api_key=PINECONE_API_KEY)
        PineconeVectorStore.from_documents(splits, embeddings, index_name=PINECONE_INDEX_NAME)

        return {"success": True, "message": f"Successfully ingested {len(splits)} chunks.", "chunks": len(splits)}

    except Exception as e:
        return {"success": False, "message": f"Ingestion failed: {str(e)}"}


def delete_document_index(user_id: int, file_name: str) -> bool:
    """Deletes all chunks for a specific file and user from Pinecone."""
    if not PINECONE_API_KEY:
        return False
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
        index.delete(filter={"user_id": user_id, "file_name": file_name.strip()})
        return True
    except Exception as e:
        print(f"Failed to delete index for {file_name}: {e}")
        return False
