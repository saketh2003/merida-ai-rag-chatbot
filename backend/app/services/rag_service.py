import json
from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.services.vector_service import vector_manager
from app.models import Message

SYSTEM_RAG_PROMPT_TEMPLATE = """You are a helpful, professional AI Assistant for the Knowledge Base Chatbot.
Answer the user's question using ONLY the provided Knowledge Base Context below.

Strict Guidelines:
1. Base your answer strictly on the provided Knowledge Base Context.
2. Do not invent, hallucinate, or assume facts not present in the context.
3. If the provided context does not contain the answer, state clearly: "I could not find relevant information in the knowledge base to answer your question."

--- KNOWLEDGE BASE CONTEXT ---
{context}
-------------------------------
"""

class RAGService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model_name = settings.GROQ_MODEL

    def get_llm(self):
        if not self.api_key:
            return None
        return ChatGroq(
            groq_api_key=self.api_key,
            model_name=self.model_name,
            temperature=0.2
        )

    def generate_response(
        self,
        prompt: str,
        chat_history: Optional[List[Message]] = None,
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        Executes RAG Retrieval pipeline:
        1. Search ChromaDB for top_k relevant chunks matching the prompt.
        2. Format retrieved context and citations metadata.
        3. Invoke Groq Llama 3 model with system prompt, context, and chat history.
        4. Return answer text and citations array.
        """
        # 1. Retrieve matching chunks from ChromaDB
        matched_chunks = vector_manager.query_similarity(query_text=prompt, top_k=top_k)

        # 2. Extract citations metadata and format context block
        citations = []
        context_blocks = []

        for idx, chunk in enumerate(matched_chunks):
            metadata = chunk.get("metadata", {})
            filename = metadata.get("filename", "Unknown Document")
            page_num = metadata.get("page_number")
            
            context_blocks.append(f"[Source: {filename}" + (f", Page {page_num}" if page_num else "") + f"]:\n{chunk['content']}")
            
            citations.append({
                "document_id": metadata.get("document_id"),
                "filename": filename,
                "content": chunk["content"],
                "page_number": page_num
            })

        context_str = "\n\n".join(context_blocks) if context_blocks else "No relevant knowledge base documents found."

        # If no context found at all, we can optimize or let LLM state not found
        system_content = SYSTEM_RAG_PROMPT_TEMPLATE.format(context=context_str)

        # 3. Construct LangChain messages sequence
        messages = [SystemMessage(content=system_content)]

        # Append past conversation history (up to last 6 messages for context memory)
        if chat_history:
            recent_history = chat_history[-6:]
            for msg in recent_history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))

        # Append current user prompt
        messages.append(HumanMessage(content=prompt))

        # 4. Invoke LLM or Fallback (for testing / unconfigured API Key)
        llm = self.get_llm()
        if llm is None:
            # Fallback for testing when GROQ_API_KEY is not set
            if not matched_chunks:
                answer = "I could not find relevant information in the knowledge base to answer your question."
            else:
                answer = f"Based on the knowledge base context from '{citations[0]['filename']}': {citations[0]['content']}"
        else:
            try:
                ai_message = llm.invoke(messages)
                answer = ai_message.content
            except Exception as e:
                answer = f"An error occurred while calling the AI model: {str(e)}"

        return {
            "answer": answer,
            "citations": citations
        }

rag_service = RAGService()
