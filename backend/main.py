"""
M.I.D.A.S. API v3.2: Sessions, Global Gallery, and RAG Ingestion.
"""
import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv

# Logic imports
from src.agent.rag_agent import RAGAgent
from src.interface.voice_service import VoiceService

load_dotenv()

app = FastAPI(title="M.I.D.A.S. API", version="3.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
IMAGES_DIR = STATIC_DIR / "generated_images"
STATIC_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Initialize
try:
    agent = RAGAgent()
    voice_service = VoiceService()
except Exception as e:
    print(f"❌ Init Error: {e}")
    agent = None
    voice_service = None

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"

class ChatResponse(BaseModel):
    text: str
    images: List[str]
    audio_url: Optional[str] = None

class TextIngestRequest(BaseModel):
    text: str
    source: str = "manual_input"

@app.get("/")
async def root():
    return {"status": "online", "agent": "M.I.D.A.S."}

@app.get("/status")
async def get_status():
    return {
        "knowledge_base": agent.get_knowledge_base_info() if agent else {},
        "models": agent.MODELS if agent else {}
    }

@app.get("/gallery")
async def get_gallery():
    try:
        images = []
        base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        files = sorted(os.listdir(IMAGES_DIR), key=lambda x: os.path.getmtime(IMAGES_DIR / x), reverse=True)
        for img_file in files:
            if img_file.lower().endswith((".png", ".jpg", ".jpeg")):
                images.append(f"{base_url}/static/generated_images/{img_file}")
        return {"images": images}
    except Exception as e:
        return {"images": [], "error": str(e)}

@app.post("/ingest/text")
async def ingest_text(request: TextIngestRequest):
    try:
        chunks = agent.doc_processor.process_text_input(request.text, request.source)
        count = agent.add_documents_from_processor(chunks)
        return {"status": "success", "added_chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/files")
async def ingest_files(files: List[UploadFile] = File(...)):
    total_chunks = 0
    temp_dir = BASE_DIR / "temp_uploads"
    temp_dir.mkdir(exist_ok=True)
    try:
        for file in files:
            file_path = temp_dir / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            chunks = agent.doc_processor.load_document(str(file_path))
            count = agent.add_documents_from_processor(chunks)
            total_chunks += count
            os.remove(file_path)
        return {"status": "success", "total_chunks": total_chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        if not agent: raise Exception("Agente no listo")
        
        result = agent.chat(request.message, thread_id=request.thread_id)
        text = result.get("text", "")
        images = result.get("images", [])
        
        audio_filename = f"voice_{os.urandom(4).hex()}.wav"
        audio_path = STATIC_DIR / audio_filename
        voice_service.speak(text, output_path=str(audio_path))
        
        base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        image_urls = [f"{base_url}/static/generated_images/{Path(img).name}" for img in images]
        audio_url = f"{base_url}/static/{audio_filename}"
        
        return ChatResponse(text=text, images=image_urls, audio_url=audio_url)
    except Exception as e:
        print(f"❌ Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)