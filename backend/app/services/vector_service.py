import os
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions

# Store persistent vector database in backend/chroma_db
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
COLLECTION_NAME = "knowledge_base"

class VectorStoreManager:
    _instance = None

    def __init__(self):
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        # Initialize persistent Chroma client
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        
        # HuggingFace all-MiniLM-L6-v2 ONNX embedding function (384-dimensional vector embeddings)
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = VectorStoreManager()
        return cls._instance

    def add_chunks(
        self,
        chunk_texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> int:
        """Embed and insert text chunks into ChromaDB vector store."""
        if not chunk_texts:
            return 0

        # Upsert chunks into ChromaDB collection with metadata
        self.collection.upsert(
            ids=ids,
            documents=chunk_texts,
            metadatas=metadatas
        )
        return len(chunk_texts)

    def delete_document_vectors(self, document_id: int) -> int:
        """Delete all chunk vectors belonging to the specified document_id."""
        try:
            results = self.collection.get(where={"document_id": document_id})
            ids_to_delete = results.get("ids", [])
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                return len(ids_to_delete)
            return 0
        except Exception as e:
            print(f"Warning: Exception deleting vectors for doc_id={document_id}: {e}")
            return 0

    def query_similarity(self, query_text: str, top_k: int = 4, document_id_filter: int = None) -> List[Dict[str, Any]]:
        """Query top_k most similar chunks from vector store."""
        where_clause = {"document_id": document_id_filter} if document_id_filter else None

        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where_clause
        )

        matched_chunks = []
        if results and results.get("documents") and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                matched_chunks.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0.0
                })
        return matched_chunks

vector_manager = VectorStoreManager.get_instance()
