"""
Vector store implementation using Qdrant for persistent RAG system.
Includes advanced retrieval techniques like MMR and Hybrid Search.
"""
import os
from typing import List, Optional, Tuple, Dict, Any

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore as LangChainQdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models


class QdrantVectorStore:
    """Persistent vector store using Qdrant Cloud/Local with advanced retrieval."""
    
    def __init__(
        self, 
        embedding_model: str = "models/gemini-embedding-001", 
        collection_name: str = "digital_product_factory",
        api_key: Optional[str] = None,
        url: Optional[str] = None
    ):
        """Initialize the Qdrant vector store."""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("Google API key is required (GOOGLE_API_KEY)")
            
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model=embedding_model, 
            google_api_key=google_api_key
        )
        
        self.url = url or os.getenv("QDRANT_URL")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "digital_product_factory")
        
        if not self.url:
            print("⚠️ QDRANT_URL not found, falling back to local memory.")
            self.client = QdrantClient(":memory:")
        else:
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
            )
            
        # Ensure collection exists with correct dimension (Gemini = 3072)
        try:
            collection_info = self.client.get_collection(self.collection_name)
            current_dim = collection_info.config.params.vectors.size
            if current_dim != 3072:
                print(f"🔄 Recreando colección '{self.collection_name}' con dimensiones correctas (3072)...")
                self.client.delete_collection(self.collection_name)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=3072, distance=models.Distance.COSINE),
                )
        except Exception:
            print(f"📦 Creando colección '{self.collection_name}' en Qdrant Cloud (3072 dimensiones)...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=3072, distance=models.Distance.COSINE),
            )
            
        self.vector_store = LangChainQdrant(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embedding_model,
        )
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to Qdrant with batching."""
        import time
        if not documents:
            return
        
        batch_size = 15
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            print(f"    - Ingesting batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}...")
            self.vector_store.add_documents(batch)
            if i + batch_size < len(documents):
                time.sleep(2)
    
    def similarity_search(self, query: str, k: int = 10, search_type: str = "mmr") -> List[Document]:
        """
        Advanced Search: 
        - 'similarity': standard vector search
        - 'mmr': Max Marginal Relevance (Relevance + Diversity)
        """
        if search_type == "mmr":
            # Fetch k=10 but diversify results
            return self.vector_store.max_marginal_relevance_search(query, k=k, fetch_k=20)
        return self.vector_store.similarity_search(query, k=k)
    
    def similarity_search_with_score(self, query: str, k: int = 10) -> List[Tuple[Document, float]]:
        """Search with scores, increasing k for more depth."""
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def clear(self) -> None:
        """Clear the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=3072, distance=models.Distance.COSINE),
            )
        except Exception as e:
            print(f"Error clearing collection: {e}")

    def get_document_count(self) -> int:
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except:
            return 0

    def __len__(self) -> int:
        return self.get_document_count()


class RAGRetriever:
    """Enhanced RAG retriever with deep context integration."""
    
    def __init__(self, vector_store: QdrantVectorStore, min_score: float = 0.35):
        self.vector_store = vector_store
        self.min_score = min_score
    
    def retrieve(self, query: str, k: int = 12) -> List[Document]:
        """Retrieve relevant and diverse documents using MMR by default."""
        # Usamos MMR para obtener profundidad y diversidad de temas
        docs = self.vector_store.similarity_search(query, k=k, search_type="mmr")
        return docs
    
    def get_context(self, query: str, max_tokens: int = 6000) -> str:
        """Get deep context string, allowing more tokens for our advanced models."""
        relevant_docs = self.retrieve(query)
        
        context_parts = []
        current_length = 0
        
        for doc in relevant_docs:
            content = doc.page_content
            source = doc.metadata.get('source', 'unknown')
            chunk_info = f"[Fragmento: {doc.metadata.get('chunk_id', '?')}/{doc.metadata.get('total_chunks', '?')}]"
            
            full_content = f"--- FUENTE: {source} {chunk_info} ---\n{content}"
            content_tokens = len(full_content) // 4
            
            if current_length + content_tokens > max_tokens:
                break
            
            context_parts.append(full_content)
            current_length += content_tokens
        
        return "\n\n".join(context_parts)
