import os
import io
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import User, Conversation, Message, Document
from app.security import hash_password
from app.services.vector_service import vector_manager

def run_phase5_integration_validation():
    print("==================================================================")
    print("🚀 STARTING PHASE 5 FULL SYSTEM END-TO-END INTEGRATION VALIDATION")
    print("==================================================================")

    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    db = SessionLocal()

    try:
        # -------------------------------------------------------------
        # 1. Health Endpoint Verification
        # -------------------------------------------------------------
        health_res = client.get("/api/v1/health")
        assert health_res.status_code == 200
        assert health_res.json()["status"] == "ok"
        print("✅ 1. Health check endpoint verified: /api/v1/health is operational.")

        # -------------------------------------------------------------
        # 2. User Registration & Admin Seeding
        # -------------------------------------------------------------
        # Admin account
        admin_email = "phase5_admin@example.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                hashed_password=hash_password("AdminPass123!"),
                full_name="Phase 5 Admin",
                role="admin",
                is_active=True
            )
            db.add(admin)

        # User A account
        user_a_email = "phase5_user_a@example.com"
        reg_a_res = client.post("/api/v1/auth/register", json={
            "email": user_a_email,
            "password": "UserAPass123!",
            "full_name": "User A"
        })
        if reg_a_res.status_code == 201:
            assert reg_a_res.json()["role"] == "user"
            print("✅ 2. Registration created standard user account with 'user' role.")
        
        # User B account
        user_b_email = "phase5_user_b@example.com"
        client.post("/api/v1/auth/register", json={
            "email": user_b_email,
            "password": "UserBPass123!",
            "full_name": "User B"
        })
        db.commit()

        # Login users & obtain JWT tokens
        admin_token = client.post("/api/v1/auth/login", json={"email": admin_email, "password": "AdminPass123!"}).json()["access_token"]
        user_a_token = client.post("/api/v1/auth/login", json={"email": user_a_email, "password": "UserAPass123!"}).json()["access_token"]
        user_b_token = client.post("/api/v1/auth/login", json={"email": user_b_email, "password": "UserBPass123!"}).json()["access_token"]

        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        user_a_headers = {"Authorization": f"Bearer {user_a_token}"}
        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

        print("✅ 3. Login with Email + Password successful; JWT Bearer tokens received.")

        # -------------------------------------------------------------
        # 3. RBAC Admin Security Checks
        # -------------------------------------------------------------
        forbidden_res = client.post(
            "/api/v1/admin/kb/upload",
            headers=user_a_headers,
            files={"file": ("unauthorized.txt", io.BytesIO(b"test"), "text/plain")}
        )
        assert forbidden_res.status_code == 403
        print("✅ 4. RBAC Security verified: Standard user rejected with 403 Forbidden on Admin KB endpoint.")

        # -------------------------------------------------------------
        # 4. Admin Knowledge Base Upload (`integration_test.txt`)
        # -------------------------------------------------------------
        kb_text = b"The company was founded in 2020. The main product is an AI-powered customer support platform. The headquarters is located in Hyderabad."
        files = {"file": ("integration_test.txt", io.BytesIO(kb_text), "text/plain")}
        
        upload_res = client.post("/api/v1/admin/kb/upload", headers=admin_headers, files=files)
        assert upload_res.status_code == 201
        doc_data = upload_res.json()
        doc_id = doc_data["id"]
        assert doc_data["status"] == "completed"
        assert doc_data["chunk_count"] >= 1
        print(f"✅ 5. Admin Knowledge Base document 'integration_test.txt' uploaded & embedded into ChromaDB (Doc ID={doc_id}).")

        # -------------------------------------------------------------
        # 5. RAG Retrieval & QA Verification
        # -------------------------------------------------------------
        conv_res = client.post("/api/v1/chat/conversations", headers=user_a_headers, json={"title": "Phase 5 Test Session"})
        conv_id = conv_res.json()["id"]

        prompt1 = "When was the company founded?"
        msg1_res = client.post(f"/api/v1/chat/conversations/{conv_id}/message", headers=user_a_headers, json={"prompt": prompt1})
        assert msg1_res.status_code == 200
        msg1_data = msg1_res.json()
        
        assert msg1_data["role"] == "assistant"
        assert "2020" in msg1_data["content"]
        assert len(msg1_data["citations"]) > 0
        assert msg1_data["citations"][0]["filename"] == "integration_test.txt"
        print(f"✅ 6. RAG Retrieval successful!\n   - Prompt: '{prompt1}'\n   - Answer: '{msg1_data['content']}'\n   - Citation: {msg1_data['citations'][0]['filename']}")

        # -------------------------------------------------------------
        # 6. RAG Knowledge Base Fallback Miss Test
        # -------------------------------------------------------------
        prompt2 = "Who won the 1920 World Series?"
        msg2_res = client.post(f"/api/v1/chat/conversations/{conv_id}/message", headers=user_a_headers, json={"prompt": prompt2})
        assert msg2_res.status_code == 200
        msg2_data = msg2_res.json()
        
        assert "could not find relevant information" in msg2_data["content"].lower()
        print(f"✅ 7. RAG Knowledge Base Fallback verified!\n   - Prompt: '{prompt2}'\n   - Answer: '{msg2_data['content']}'")

        # -------------------------------------------------------------
        # 7. Conversation History & User Isolation Tests
        # -------------------------------------------------------------
        # User A fetches conversation history
        hist_res = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=user_a_headers)
        assert hist_res.status_code == 200
        assert len(hist_res.json()["messages"]) == 4
        print("✅ 8. Conversation persistence verified: All 4 messages restored from SQLite.")

        # User B attempts to access User A's conversation -> HTTP 404
        user_b_isolation_res = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=user_b_headers)
        assert user_b_isolation_res.status_code == 404
        print("✅ 9. User Isolation verified: User B cannot access or view User A's conversation (HTTP 404).")

        # -------------------------------------------------------------
        # 8. Document & Conversation Deletion Tests
        # -------------------------------------------------------------
        del_conv_res = client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=user_a_headers)
        assert del_conv_res.status_code == 200

        del_doc_res = client.delete(f"/api/v1/admin/kb/documents/{doc_id}", headers=admin_headers)
        assert del_doc_res.status_code == 200
        print("✅ 10. Deletion functionality verified: Conversation and Knowledge Base vectors cleaned up cleanly.")

        print("\n==================================================================")
        print("🎉 ALL PHASE 5 INTEGRATION VALIDATION CHECKS COMPLETED WITH 100% SUCCESS!")
        print("==================================================================\n")

    finally:
        db.close()

if __name__ == "__main__":
    run_phase5_integration_validation()
