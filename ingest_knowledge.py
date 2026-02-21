"""
Script to ingest the Millionaire Prompts PDF into Qdrant Cloud.
"""
import os
from dotenv import load_dotenv
from src.rag import DocumentProcessor, QdrantVectorStore

def main():
    load_dotenv()
    print("🚀 Iniciando Ingesta de Conocimiento Millonario...")
    
    # 1. Configurar Procesador y Vector Store
    processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
    vector_store = QdrantVectorStore()
    
    pdf_path = "docs/Copia de PROMPTS MILLONARIOS PRO.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: No se encontró el archivo en {pdf_path}")
        return

    # 2. Cargar y Procesar el PDF
    print(f"📄 Procesando: {pdf_path}")
    chunks = processor.load_document(pdf_path)
    print(f"✅ Documento dividido en {len(chunks)} fragmentos.")

    # 3. Subir a Qdrant Cloud
    print(f"📤 Subiendo a Qdrant Cloud (AWS sa-east-1)...")
    vector_store.add_documents(chunks)
    
    print("\n✨ ¡PROCESO COMPLETADO!")
    print(f"📊 Total de fragmentos en la nube: {vector_store.get_document_count()}")
    print("JARVIS ahora tiene acceso permanente a tus Prompts Millonarios.")

if __name__ == "__main__":
    main()