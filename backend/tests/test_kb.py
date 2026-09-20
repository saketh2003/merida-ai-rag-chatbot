import io
import pytest
from app.models import User, Document
from app.security import hash_password
from app.services.vector_service import vector_manager

@pytest.fixture
def admin_headers(client, db_session):
    """Fixture creating an admin user and returning auth headers."""
    admin_user = User(
        email="admin_kb_test@example.com",
        hashed_password=hash_password("adminpass123"),
        full_name="KB Admin",
        role="admin",
        is_active=True
    )
    db_session.add(admin_user)
    db_session.commit()

    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin_kb_test@example.com",
        "password": "adminpass123"
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def user_headers(client, db_session):
    """Fixture creating a standard non-admin user and returning auth headers."""
    normal_user = User(
        email="standard_user@example.com",
        hashed_password=hash_password("userpass123"),
        full_name="Standard User",
        role="user",
        is_active=True
    )
    db_session.add(normal_user)
    db_session.commit()

    login_res = client.post("/api/v1/auth/login", json={
        "email": "standard_user@example.com",
        "password": "userpass123"
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_admin_upload_txt_document_success(client, admin_headers):
    file_content = b"Artificial Intelligence and Retrieval Augmented Generation (RAG) enhance LLM accuracy by incorporating domain knowledge."
    files = {"file": ("test_rag_info.txt", io.BytesIO(file_content), "text/plain")}

    response = client.post("/api/v1/admin/kb/upload", headers=admin_headers, files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test_rag_info.txt"
    assert data["status"] == "completed"
    assert data["chunk_count"] >= 1

    # Verify vector store contains chunks for this document
    doc_id = data["id"]
    query_results = vector_manager.query_similarity("Retrieval Augmented Generation", top_k=2, document_id_filter=doc_id)
    assert len(query_results) >= 1
    assert "Retrieval Augmented Generation" in query_results[0]["content"]

def test_admin_upload_invalid_format_fails(client, admin_headers):
    file_content = b"binary exe content"
    files = {"file": ("malicious.exe", io.BytesIO(file_content), "application/octet-stream")}

    response = client.post("/api/v1/admin/kb/upload", headers=admin_headers, files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

def test_non_admin_cannot_access_kb_endpoints(client, user_headers):
    file_content = b"Test document text"
    files = {"file": ("user_doc.txt", io.BytesIO(file_content), "text/plain")}

    # 1. Upload forbidden
    res_upload = client.post("/api/v1/admin/kb/upload", headers=user_headers, files=files)
    assert res_upload.status_code == 403

    # 2. List forbidden
    res_list = client.get("/api/v1/admin/kb/documents", headers=user_headers)
    assert res_list.status_code == 403

    # 3. Delete forbidden
    res_delete = client.delete("/api/v1/admin/kb/documents/1", headers=user_headers)
    assert res_delete.status_code == 403

def test_admin_list_documents(client, admin_headers):
    # Upload two documents
    files1 = {"file": ("doc1.txt", io.BytesIO(b"Document one content."), "text/plain")}
    files2 = {"file": ("doc2.txt", io.BytesIO(b"Document two content."), "text/plain")}

    client.post("/api/v1/admin/kb/upload", headers=admin_headers, files=files1)
    client.post("/api/v1/admin/kb/upload", headers=admin_headers, files=files2)

    res = client.get("/api/v1/admin/kb/documents", headers=admin_headers)
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) >= 2
    filenames = [d["filename"] for d in docs]
    assert "doc1.txt" in filenames
    assert "doc2.txt" in filenames

def test_admin_delete_document_removes_vectors_and_record(client, admin_headers):
    files = {"file": ("to_delete.txt", io.BytesIO(b"This document will be deleted from KB."), "text/plain")}
    upload_res = client.post("/api/v1/admin/kb/upload", headers=admin_headers, files=files)
    doc_id = upload_res.json()["id"]

    # Verify vector exists before deletion
    results_before = vector_manager.query_similarity("deleted from KB", top_k=2, document_id_filter=doc_id)
    assert len(results_before) >= 1

    # Delete document
    del_res = client.delete(f"/api/v1/admin/kb/documents/{doc_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json()["document_id"] == doc_id

    # Verify vector is deleted from ChromaDB
    results_after = vector_manager.query_similarity("deleted from KB", top_k=2, document_id_filter=doc_id)
    assert len(results_after) == 0

    # Verify record is deleted from DB
    list_res = client.get("/api/v1/admin/kb/documents", headers=admin_headers)
    doc_ids = [d["id"] for d in list_res.json()]
    assert doc_id not in doc_ids
