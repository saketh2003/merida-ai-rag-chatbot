import os
import shutil
from typing import List, Dict, Any, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pypdf
import docx2txt

from app.models import Document
from app.services.vector_service import vector_manager

# Local storage paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

def ensure_uploads_dir():
    os.makedirs(UPLOADS_DIR, exist_ok=True)

def validate_uploaded_file(file: UploadFile) -> str:
    """Validate file extension and ensure file is non-empty."""
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: PDF, TXT, DOCX."
        )
    return ext

def save_uploaded_file(file: UploadFile, document_id: int) -> str:
    """Save uploaded file stream to local disk."""
    ensure_uploads_dir()
    filename = file.filename or "uploaded_file"
    safe_filename = f"doc_{document_id}_{filename}"
    file_path = os.path.join(UPLOADS_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path

def extract_text_chunks(file_path: str, ext: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Extract raw text from PDF, TXT, or DOCX file and split into semantic chunks.
    Returns list of tuples: (chunk_text, metadata_dict)
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    raw_sections = []  # tuples of (text, page_number_or_none)

    if ext == ".pdf":
        reader = pypdf.PdfReader(file_path)
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                raw_sections.append((page_text, page_idx + 1))
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
            if text.strip():
                raw_sections.append((text, None))
    elif ext == ".docx":
        text = docx2txt.process(file_path) or ""
        if text.strip():
            raw_sections.append((text, None))

    if not raw_sections:
        raise ValueError("No extractable text found in uploaded document.")

    all_chunks = []
    global_chunk_idx = 0

    for section_text, page_num in raw_sections:
        chunks = splitter.split_text(section_text)
        for chunk in chunks:
            if chunk.strip():
                metadata = {"chunk_index": global_chunk_idx}
                if page_num is not None:
                    metadata["page_number"] = page_num
                all_chunks.append((chunk, metadata))
                global_chunk_idx += 1

    return all_chunks

def process_and_embed_document(document: Document, db: Session) -> Document:
    """
    Process document file: extract text, generate chunks, embed & store in ChromaDB,
    and update database record status.
    """
    ext = os.path.splitext(document.filename)[1].lower()
    
    try:
        # Extract text chunks and page metadata
        extracted_chunks = extract_text_chunks(document.file_path, ext)
        
        chunk_texts = []
        metadatas = []
        ids = []

        for idx, (chunk_text, meta) in enumerate(extracted_chunks):
            chunk_texts.append(chunk_text)
            chunk_meta = {
                "document_id": document.id,
                "filename": document.filename,
                "chunk_index": idx,
            }
            if "page_number" in meta:
                chunk_meta["page_number"] = meta["page_number"]
            metadatas.append(chunk_meta)
            ids.append(f"doc_{document.id}_chunk_{idx}")

        # Add chunks to ChromaDB vector store
        added_count = vector_manager.add_chunks(chunk_texts, metadatas, ids)

        # Update SQLite document record
        document.status = "completed"
        document.chunk_count = added_count
        document.error_message = None
        db.commit()
        db.refresh(document)
        return document

    except Exception as e:
        db.rollback()
        document.status = "failed"
        document.chunk_count = 0
        document.error_message = str(e)
        db.commit()
        db.refresh(document)
        return document

def delete_document_file_and_vectors(document: Document, db: Session):
    """
    Delete document file from disk, delete vectors from ChromaDB, and remove record from DB.
    """
    # 1. Delete vectors from ChromaDB
    vector_manager.delete_document_vectors(document.id)

    # 2. Delete file from local disk if it exists
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            print(f"Warning: Could not delete file {document.file_path}: {e}")

    # 3. Delete database record
    db.delete(document)
    db.commit()
