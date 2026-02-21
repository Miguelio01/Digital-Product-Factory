"""
Advanced Document processing with metadata enrichment inspired by LlamaIndex.
"""
import os
from typing import List, Dict, Any
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class DocumentProcessor:
    """Enhanced process and prepare documents with semantic metadata."""
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
    
    def load_document(self, file_path: str) -> List[Document]:
        """Load a document and enrich it with metadata."""
        file_extension = Path(file_path).suffix.lower()
        source_name = Path(file_path).name
        
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
            documents = loader.load()
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

        # Split into semantic chunks
        split_docs = self.text_splitter.split_documents(documents)
        
        # Enrich each chunk with LlamaIndex-style metadata
        for i, doc in enumerate(split_docs):
            doc.metadata.update({
                "source": source_name,
                "chunk_id": i,
                "total_chunks": len(split_docs),
                "ingestion_date": os.environ.get("CURRENT_DATE", "2026-02-15")
            })
            
        return split_docs
    
    def process_text_input(self, text: str, source: str = "text_input") -> List[Document]:
        """Process raw text input with metadata."""
        document = Document(
            page_content=text,
            metadata={"source": source, "type": "text"}
        )
        return self.text_splitter.split_documents([document])