import os
import sys
import io
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import User, Document
from app.security import hash_password
from app.services.vector_service import vector_manager

def run_phase2_verification():
    print("🚀 Starting Phase 2 Manual Verification Script...")
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)

    db = SessionLocal()
    try:
        # 1. Ensure Admin User
        admin_email = "admin_verify@example.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                hashed_password=hash_password("AdminVerify123!"),
                full_name="Phase2 Verifier Admin",
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.commit()

        # 2. Login Admin
        login_res = client.post("/api/v1/auth/login", json={"email": admin_email, "password": "AdminVerify123!"})
        assert login_res.status_code == 200, "Admin login failed"
        admin_token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        print("✅ Admin authenticated successfully.")

        # 3. Upload Sample TXT Document
        sample_text = b"FastAPI combined with ChromaDB and HuggingFace Embeddings provides a robust foundation for RAG applications."
        files = {"file": ("manual_verify_doc.txt", io.BytesIO(sample_text), "text/plain")}
        upload_res = client.post("/api/v1/admin/kb/upload", headers=headers, files=files)
        assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
        doc_data = upload_res.json()
        doc_id = doc_data["id"]
        print(f"✅ Document uploaded & parsed successfully (ID={doc_id}, Status={doc_data['status']}, Chunks={doc_data['chunk_count']}).")

        # 4. Verify Document in SQLite
        db_doc = db.query(Document).filter(Document.id == doc_id).first()
        assert db_doc is not None and db_doc.status == "completed", "Document not found in SQLite"
        print("✅ Document status verified in SQLite database.")

        # 5. Query ChromaDB Vector Similarity
        similarity_results = vector_manager.query_similarity("HuggingFace Embeddings RAG", top_k=1, document_id_filter=doc_id)
        assert len(similarity_results) > 0, "No vectors found in ChromaDB!"
        print(f"✅ ChromaDB Vector retrieval verified! Matched text snippet: '{similarity_results[0]['content'][:60]}...'")

        # 6. Verify List Endpoint
        list_res = client.get("/api/v1/admin/kb/documents", headers=headers)
        assert list_res.status_code == 200
        listed_ids = [d["id"] for d in list_res.json()]
        assert doc_id in listed_ids, "Uploaded document missing from list endpoint"
        print("✅ Document list endpoint verified.")

        # 7. Delete Document & Verify Vector Cleanup
        del_res = client.delete(f"/api/v1/admin/kb/documents/{doc_id}", headers=headers)
        assert del_res.status_code == 200, "Delete endpoint failed"
        
        post_del_vectors = vector_manager.query_similarity("HuggingFace Embeddings RAG", top_k=1, document_id_filter=doc_id)
        assert len(post_del_vectors) == 0, "Vectors were not deleted from ChromaDB!"
        print("✅ Document and ChromaDB vectors deleted successfully.")

        print("\n🎉 ALL PHASE 2 VERIFICATION CHECKS PASSED PERFECTLY!\n")

    finally:
        db.close()

if __name__ == "__main__":
    run_phase2_verification()
