import os
import sys
import io
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import User, Conversation, Message, Document
from app.security import hash_password
from app.services.vector_service import vector_manager

def run_phase3_verification():
    print("🚀 Starting Phase 3 End-to-End Verification Script...")
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)

    db = SessionLocal()
    try:
        # 1. Ensure Admin and User accounts
        admin_email = "rag_admin@example.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                hashed_password=hash_password("AdminPass123!"),
                full_name="RAG System Admin",
                role="admin",
                is_active=True
            )
            db.add(admin)

        user_email = "rag_user@example.com"
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            user = User(
                email=user_email,
                hashed_password=hash_password("UserPass123!"),
                full_name="RAG Regular User",
                role="user",
                is_active=True
            )
            db.add(user)
        db.commit()

        # 2. Login Admin & Upload Document
        admin_token = client.post("/api/v1/auth/login", json={"email": admin_email, "password": "AdminPass123!"}).json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        kb_text = b"Groq Llama 3 API provides sub-second inference speeds, enabling ultra-fast retrieval augmented generation for enterprises."
        files = {"file": ("groq_info.txt", io.BytesIO(kb_text), "text/plain")}
        upload_res = client.post("/api/v1/admin/kb/upload", headers=admin_headers, files=files)
        assert upload_res.status_code == 201
        print("✅ Step 1: Admin uploaded document into ChromaDB knowledge base.")

        # 3. Login User & Create Conversation
        user_token = client.post("/api/v1/auth/login", json={"email": user_email, "password": "UserPass123!"}).json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        conv_res = client.post("/api/v1/chat/conversations", headers=user_headers, json={"title": "RAG Verification Session"})
        conv_id = conv_res.json()["id"]
        print(f"✅ Step 2: Regular user created conversation session (ID={conv_id}).")

        # 4. Send Query Matching KB
        prompt1 = "What is the speed advantage of Groq Llama 3 API?"
        msg1_res = client.post(f"/api/v1/chat/conversations/{conv_id}/message", headers=user_headers, json={"prompt": prompt1})
        assert msg1_res.status_code == 200
        data1 = msg1_res.json()
        assert data1["role"] == "assistant"
        assert len(data1["citations"]) > 0
        print(f"✅ Step 3: RAG Query 1 succeeded!\n   - User: '{prompt1}'\n   - Assistant Answer: '{data1['content'][:120]}...'\n   - Citations: {data1['citations'][0]['filename']}")

        # 5. Send Query NOT in KB (Fallback check)
        prompt2 = "Who won the 1920 World Series in baseball?"
        msg2_res = client.post(f"/api/v1/chat/conversations/{conv_id}/message", headers=user_headers, json={"prompt": prompt2})
        assert msg2_res.status_code == 200
        data2 = msg2_res.json()
        assert "could not find relevant information" in data2["content"].lower()
        print(f"✅ Step 4: Unmatched RAG Query 2 fallback verified!\n   - User: '{prompt2}'\n   - Assistant Answer: '{data2['content']}'")

        # 6. Verify User Conversation History in SQLite
        history_res = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=user_headers)
        assert history_res.status_code == 200
        history = history_res.json()["messages"]
        assert len(history) == 4  # 2 user prompts + 2 assistant responses
        print("✅ Step 5: Saved message history verified in SQLite database.")

        print("\n🎉 ALL PHASE 3 VERIFICATION CHECKS PASSED PERFECTLY!\n")

    finally:
        db.close()

if __name__ == "__main__":
    run_phase3_verification()
