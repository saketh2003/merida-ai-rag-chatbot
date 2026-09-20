import os
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_admin
from app.models import User, Document
from app.schemas import DocumentResponse
from app.services.kb_service import (
    validate_uploaded_file,
    save_uploaded_file,
    process_and_embed_document,
    delete_document_file_and_vectors
)

router = APIRouter(prefix="/admin/kb", tags=["Admin Knowledge Base"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_knowledge_base_document(
    file: UploadFile = File(...),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin Endpoint: Upload a PDF, TXT, or DOCX document to the knowledge base.
    Parses document, chunks text, embeds chunks into ChromaDB, and records metadata in SQLite.
    """
    # 1. Validate file format
    ext = validate_uploaded_file(file)
    filename = file.filename or "uploaded_document"
    
    # Measure file size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

    # 2. Create database document record with 'processing' status
    doc_record = Document(
        uploaded_by_id=admin_user.id,
        filename=filename,
        file_path="pending",  # Temporary placeholder until file is saved
        file_size=file_size,
        status="processing",
        chunk_count=0
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # 3. Save file to disk
    file_path = save_uploaded_file(file, doc_record.id)
    doc_record.file_path = file_path
    db.commit()

    # 4. Extract, chunk, embed, and update document status
    processed_doc = process_and_embed_document(doc_record, db)
    return processed_doc

@router.get("/documents", response_model=List[DocumentResponse])
def list_knowledge_base_documents(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin Endpoint: List all knowledge base documents and their ingestion status."""
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return documents

@router.delete("/documents/{document_id}")
def delete_knowledge_base_document(
    document_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin Endpoint: Delete a knowledge base document.
    Removes document chunks from ChromaDB vector store, deletes file from disk, and removes database record.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found."
        )

    delete_document_file_and_vectors(document, db)
    return {
        "message": "Document deleted successfully",
        "document_id": document_id
    }
