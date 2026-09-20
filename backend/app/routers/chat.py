import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import User, Conversation, Message
from app.schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse
)
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["Chat & Conversations"])

def get_user_conversation_or_404(conversation_id: int, user_id: int, db: Session) -> Conversation:
    """Helper ensuring conversation exists and strictly belongs to current authenticated user."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found."
        )
    return conv

@router.get("/conversations", response_model=List[ConversationResponse])
def list_user_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch all conversations owned by current authenticated user."""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    return conversations

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_in: ConversationCreate = ConversationCreate(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat conversation session for current authenticated user."""
    title = conv_in.title if conv_in.title and conv_in.title.strip() else "New Conversation"
    new_conv = Conversation(
        user_id=current_user.id,
        title=title
    )
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    return new_conv

@router.get("/conversations/{conversation_id}")
def get_conversation_details(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch details and full message history of a specific conversation owned by current user."""
    conv = get_user_conversation_or_404(conversation_id, current_user.id, db)
    
    messages = db.query(Message).filter(
        Message.conversation_id == conv.id
    ).order_by(Message.created_at.asc()).all()

    messages_data = []
    for msg in messages:
        citations_parsed = None
        if msg.citations:
            try:
                citations_parsed = json.loads(msg.citations)
            except Exception:
                citations_parsed = msg.citations

        messages_data.append({
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "role": msg.role,
            "content": msg.content,
            "citations": citations_parsed,
            "created_at": msg.created_at
        })

    return {
        "id": conv.id,
        "user_id": conv.user_id,
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": messages_data
    }

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation and all its message history."""
    conv = get_user_conversation_or_404(conversation_id, current_user.id, db)
    db.delete(conv)
    db.commit()
    return {
        "message": "Conversation deleted successfully",
        "id": conversation_id
    }

@router.post("/conversations/{conversation_id}/message", response_model=MessageResponse)
def send_chat_message(
    conversation_id: int,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a prompt message to RAG Chatbot:
    1. Validate conversation ownership.
    2. Save user prompt message to SQLite.
    3. Retrieve past messages for chat memory context.
    4. Run RAG retrieval (ChromaDB + Groq LLM).
    5. Save assistant response & citations to SQLite.
    6. Return complete assistant answer JSON.
    """
    conv = get_user_conversation_or_404(conversation_id, current_user.id, db)

    prompt = msg_in.prompt.strip()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt text cannot be empty."
        )

    # Auto-update conversation title from initial user prompt if default
    if conv.title == "New Conversation":
        auto_title = prompt[:35] + ("..." if len(prompt) > 35 else "")
        conv.title = auto_title
        db.commit()

    # Save user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=prompt
    )
    db.add(user_msg)
    db.commit()

    # Fetch chat history
    history = db.query(Message).filter(
        Message.conversation_id == conv.id
    ).order_by(Message.created_at.asc()).all()

    # Execute RAG Service
    rag_result = rag_service.generate_response(prompt=prompt, chat_history=history)
    answer = rag_result["answer"]
    citations = rag_result["citations"]

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=answer,
        citations=json.dumps(citations) if citations else None
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    # Return dict with parsed citations array for structured JSON response
    return {
        "id": assistant_msg.id,
        "conversation_id": assistant_msg.conversation_id,
        "role": assistant_msg.role,
        "content": assistant_msg.content,
        "citations": citations if citations else None,
        "created_at": assistant_msg.created_at
    }
