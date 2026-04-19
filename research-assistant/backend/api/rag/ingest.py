import os
import base64
import time
from typing import Optional
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

# Local utility
from api.utils.vision_ocr import process_image_with_groq_vision

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "research-assistant")

# Embedding dimension for "llama-text-embed-v2"
EMBEDDING_MODEL = "llama-text-embed-v2"
EMBEDDING_DIMENSION = 1024


def get_embeddings():
    """Returns the Pinecone Integrated embedding model instance."""
    return PineconeEmbeddings(model=EMBEDDING_MODEL, pinecone_api_key=PINECONE_API_KEY)


def ensure_pinecone_index():
    """Creates the Pinecone index if it doesn't already exist."""
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Creating Pinecone index '{PINECONE_INDEX_NAME}'...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print("Index created successfully.")
    else:
        print(f"Pinecone index '{PINECONE_INDEX_NAME}' already exists.")
    return pc.Index(PINECONE_INDEX_NAME)


def _add_file_metadata(documents: list[Document], file_name: str) -> list[Document]:
    """Annotate each document chunk with original filename for retrieval filtering."""
    enriched_docs = []
    for doc in documents:
        metadata = dict(doc.metadata or {})
        metadata["file_name"] = file_name
        enriched_docs.append(Document(page_content=doc.page_content, metadata=metadata))
    return enriched_docs


def ingest_documents(pdf_path: str, original_file_name: Optional[str] = None) -> dict:
    """
    Loads a PDF. If it's a scan (no text), it uses Groq Vision OCR as a fallback.
    """
    if not PINECONE_API_KEY:
        return {"success": False, "message": "PINECONE_API_KEY is not set in your .env file."}

    try:
        # 1. Load with PyMuPDF
        loader = PyMuPDFLoader(pdf_path)
        documents = loader.load()

        if not documents:
            return {"success": False, "message": "Could not extract any pages from the PDF."}

        # 2. Check for text
        total_text_len = sum(len(doc.page_content.strip()) for doc in documents)
        is_scanned = total_text_len < 50  # Very little text usually means it's a scan or mostly diagrams

        file_name = original_file_name or os.path.basename(pdf_path)
        final_docs = _add_file_metadata(documents, file_name)

        if is_scanned:
            print("PDF appears to be a scan or image-based. Switching to Groq Vision OCR fallback...")
            # We need to re-open with fitz directly to get images
            import fitz
            doc = fitz.open(pdf_path)
            vision_transcriptions = []

            for i, page in enumerate(doc):
                print(f"Vision-processing page {i+1}/{len(doc)}...")
                # Render page to high-res image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                base64_img = base64.b64encode(img_data).decode('utf-8')

                # Call Groq Vision
                transcription = process_image_with_groq_vision(base64_img)
                vision_transcriptions.append(
                    Document(
                        page_content=transcription,
                        metadata={
                            "page": i + 1,
                            "source": pdf_path,
                            "method": "groq-vision-ocr",
                            "file_name": file_name,
                        }
                    )
                )
                # Small sleep to be kind to rate limits
                time.sleep(0.5)

            final_docs = vision_transcriptions
            doc.close()

        # 3. Split and Ingest
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        splits = text_splitter.split_documents(final_docs)

        if not splits:
            return {"success": False, "message": "No content could be extracted even with Vision OCR fallback."}

        ensure_pinecone_index()

        embeddings = get_embeddings()
        PineconeVectorStore.from_documents(
            documents=splits,
            embedding=embeddings,
            index_name=PINECONE_INDEX_NAME,
            pinecone_api_key=PINECONE_API_KEY,
        )

        method_text = "Vision OCR" if is_scanned else "Text Extraction"
        return {
            "success": True,
            "message": f"Successfully ingested {len(splits)} chunks from {len(documents)} pages (via {method_text}).",
            "chunks": len(splits),
            "pages": len(documents),
            "file_name": file_name,
        }

    except Exception as e:
        print(f"Ingestion error: {e}")
        return {"success": False, "message": f"Ingestion failed: {str(e)}"}
