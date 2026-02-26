"""
S.O.M.A. API v7.1: Social Orchestration & Marketing Automation.
Clean Version: Focused on Core Reasoning and OpenCanvas.
"""
import os
import shutil
import uuid
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv

# Logic imports
from src.agent.rag_agent import RAGAgent

load_dotenv()

app = FastAPI(title="S.O.M.A. API", version="7.1.0")

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

# Initialize Agent
try:
    agent = RAGAgent()
    print("🧠 S.O.M.A. Core Engine: Online")
except Exception as e:
    print(f"❌ S.O.M.A. Init Error: {e}")
    agent = None

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"

class ArtifactModel(BaseModel):
    id: str
    type: str
    content: str
    status: str

class ChatResponse(BaseModel):
    text: str
    images: List[str]
    plan: Optional[Dict[str, Any]] = None
    artifacts: Optional[List[ArtifactModel]] = None
    research: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None

class TextIngestRequest(BaseModel):
    text: str
    source: str = "manual_input"

@app.get("/")
async def root():
    return {"status": "online", "agent": "S.O.M.A. v7.1"}

@app.get("/status")
async def get_status():
    if not agent:
        return {"status": "error", "message": "Agent not initialized"}
    return {
        "knowledge_base": agent.get_knowledge_base_info(),
        "models": agent.MODELS
    }

@app.get("/history/{thread_id}")
async def get_history(thread_id: str):
    try:
        if not agent: return {"history": []}
        history = agent.get_conversation_history(thread_id)
        return {"history": history}
    except Exception as e:
        # Fallback seguro para evitar error 500
        print(f"⚠️ History Error: {e}")
        return {"history": []}

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

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        if not agent: raise HTTPException(status_code=500, detail="Agente S.O.M.A. no listo")
        
        clean_message = request.message.strip()
        if not clean_message:
            return ChatResponse(text="CORNELIO espera tus instrucciones.", images=[])
        
        # El nuevo Agente v8 maneja su propio bucle asíncrono internamente por ahora
        result = agent.chat(clean_message, thread_id=request.thread_id)
        
        return ChatResponse(
            text=result.get("text", ""),
            images=[],
            plan=None,
            artifacts=result.get("artifacts", []),
            research=None,
            reasoning=result.get("reasoning", "Autonomous Loop Active")
        )
    except Exception as e:
        print(f"❌ Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
