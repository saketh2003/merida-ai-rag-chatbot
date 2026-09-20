import io
import pytest
from app.models import User, Conversation, Message
from app.security import hash_password
from app.services.vector_service import vector_manager

@pytest.fixture
def user_a(client, db_session):
    user = User(
        email="usera_chat@example.com",
        hashed_password=hash_password("pass123"),
        full_name="User A",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    login_res = client.post("/api/v1/auth/login", json={"email": "usera_chat@example.com", "password": "pass123"})
    token = login_res.json()["access_token"]
    return {"headers": {"Authorization": f"Bearer {token}"}, "user": user}

@pytest.fixture
def user_b(client, db_session):
    user = User(
        email="userb_chat@example.com",
        hashed_password=hash_password("pass123"),
        full_name="User B",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    login_res = client.post("/api/v1/auth/login", json={"email": "userb_chat@example.com", "password": "pass123"})
    token = login_res.json()["access_token"]
    return {"headers": {"Authorization": f"Bearer {token}"}, "user": user}

@pytest.fixture
def admin_headers(client, db_session):
    admin = User(
        email="admin_rag_chat@example.com",
        hashed_password=hash_password("adminpass123"),
        full_name="RAG Admin",
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()

    login_res = client.post("/api/v1/auth/login", json={"email": "admin_rag_chat@example.com", "password": "adminpass123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_and_list_conversations(client, user_a):
    headers = user_a["headers"]

    # 1. Create conversation
    res_create = client.post("/api/v1/chat/conversations", headers=headers, json={"title": "Python Architecture Chat"})
    assert res_create.status_code == 201
    conv = res_create.json()
    assert conv["title"] == "Python Architecture Chat"
    conv_id = conv["id"]

    # 2. List conversations
    res_list = client.get("/api/v1/chat/conversations", headers=headers)
    assert res_list.status_code == 200
    conv_list = res_list.json()
    assert len(conv_list) >= 1
    assert conv_list[0]["id"] == conv_id

def test_user_conversation_isolation(client, user_a, user_b):
    headers_a = user_a["headers"]
    headers_b = user_b["headers"]

    # User A creates a conversation
    res_a = client.post("/api/v1/chat/conversations", headers=headers_a, json={"title": "User A Private Chat"})
    conv_a_id = res_a.json()["id"]

    # User B lists conversations -> User A's conversation should NOT be in User B's list
    res_b_list = client.get("/api/v1/chat/conversations", headers=headers_b)
    assert res_b_list.status_code == 200
    b_conv_ids = [c["id"] for c in res_b_list.json()]
    assert conv_a_id not in b_conv_ids

    # User B attempts to GET User A's conversation -> HTTP 404
    res_b_get = client.get(f"/api/v1/chat/conversations/{conv_a_id}", headers=headers_b)
    assert res_b_get.status_code == 404

    # User B attempts to DELETE User A's conversation -> HTTP 404
    res_b_del = client.delete(f"/api/v1/chat/conversations/{conv_a_id}", headers=headers_b)
    assert res_b_del.status_code == 404

    # User B attempts to send message to User A's conversation -> HTTP 404
    res_b_msg = client.post(f"/api/v1/chat/conversations/{conv_a_id}/message", headers=headers_b, json={"prompt": "Hacking chat"})
    assert res_b_msg.status_code == 404

def test_delete_conversation(client, user_a):
    headers = user_a["headers"]
    res_create = client.post("/api/v1/chat/conversations", headers=headers, json={"title": "To Delete"})
    conv_id = res_create.json()["id"]

    res_del = client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=headers)
    assert res_del.status_code == 200

    res_get = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers)
    assert res_get.status_code == 404

def test_rag_message_empty_kb_context_response(client, user_a):
    headers = user_a["headers"]
    res_create = client.post("/api/v1/chat/conversations", headers=headers, json={"title": "Unmatched Query"})
    conv_id = res_create.json()["id"]

    # Ask a question when vector store is empty / unmatched
    res_msg = client.post(f"/api/v1/chat/conversations/{conv_id}/message", headers=headers, json={"prompt": "What is the secret code of Atlantis?"})
    assert res_msg.status_code == 200
    msg_data = res_msg.json()
    assert msg_data["role"] == "assistant"
    assert "could not find relevant information" in msg_data["content"].lower()

def test_rag_message_with_knowledge_base_retrieval(client, admin_headers, user_a):
    # 1. Admin uploads document to KB
    file_content = b"LangChain and Groq LLM integration allows developers to build high-performance RAG pipelines."
    files = {"file": ("langchain_groq_spec.txt", io.BytesIO(file_content), "text/plain")}
    client.post("/api/v1/admin/kb/upload", headers=admin_headers, files=files)

    # 2. User A sends prompt matching KB topic
    headers = user_a["headers"]
    res_create = client.post("/api/v1/chat/conversations", headers=headers, json={"title": "RAG Spec Chat"})
    conv_id = res_create.json()["id"]

    res_msg = client.post(f"/api/v1/chat/conversations/{conv_id}/message", headers=headers, json={"prompt": "How do LangChain and Groq LLM work together?"})
    assert res_msg.status_code == 200
    msg_data = res_msg.json()

    assert msg_data["role"] == "assistant"
    assert len(msg_data["citations"]) > 0
    assert msg_data["citations"][0]["filename"] == "langchain_groq_spec.txt"

    # 3. Check full conversation history includes both user and assistant messages
    res_details = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers)
    assert res_details.status_code == 200
    details = res_details.json()
    assert len(details["messages"]) == 2
    assert details["messages"][0]["role"] == "user"
    assert details["messages"][1]["role"] == "assistant"
