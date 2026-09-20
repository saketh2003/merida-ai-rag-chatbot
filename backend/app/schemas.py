import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None

# Health Schema
class HealthResponse(BaseModel):
    status: str
    database: str
    version: str = "1.0.0"

# Conversation & Message Schemas
class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(BaseModel):
    prompt: str

class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    citations: Optional[Any] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Document Schema
class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    chunk_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
