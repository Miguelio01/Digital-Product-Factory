"""
Vector store implementation using Qdrant for persistent RAG system.
Includes multi-venture metadata filtering.
"""
import os
from typing import List, Optional, Tuple, Dict, Any

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore as LangChainQdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models


class QdrantVectorStore:
    """Persistent vector store using Qdrant with Multi-Venture filtering."""
    
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
            self.client = QdrantClient(url=self.url, api_key=self.api_key)
            
        # Ensure collection exists
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            print(f"📦 Creando colección '{self.collection_name}' (3072 dimensiones)...")
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
        """Add documents with metadata."""
        if not documents: return
        self.vector_store.add_documents(documents)
    
    def similarity_search(self, query: str, k: int = 10, venture_id: Optional[str] = None) -> List[Document]:
        """
        Search with Multi-Venture Filter.
        Returns: current venture + global knowledge + legacy (null) knowledge.
        """
        search_filter = None
        if venture_id and venture_id != "General":
            # Filtro: (venture_id == actual) OR (venture_id == "global") OR (venture_id == null)
            search_filter = models.Filter(
                should=[
                    models.FieldCondition(key="metadata.venture_id", match=models.MatchValue(value=venture_id)),
                    models.FieldCondition(key="metadata.venture_id", match=models.MatchValue(value="global")),
                    models.IsNullCondition(key="metadata.venture_id")
                ]
            )
        
        return self.vector_store.similarity_search(query, k=k, filter=search_filter)
    
    def get_document_count(self) -> int:
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except:
            return 0

class RAGRetriever:
    """Retriever with Multi-Venture context isolation."""
    
    def __init__(self, vector_store: QdrantVectorStore):
        self.vector_store = vector_store
    
    def get_context(self, query: str, venture_id: Optional[str] = None, max_tokens: int = 4000) -> str:
        """Get context filtered by venture."""
        relevant_docs = self.vector_store.similarity_search(query, k=8, venture_id=venture_id)
        
        context_parts = []
        for doc in relevant_docs:
            source = doc.metadata.get('source', 'Manual')
            v_id = doc.metadata.get('venture_id', 'global')
            context_parts.append(f"--- FUENTE [{v_id}]: {source} ---\n{doc.page_content}")
        
        return "\n\n".join(context_parts)
