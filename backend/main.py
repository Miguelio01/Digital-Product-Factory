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
from src.agent.rag_agent import CornelioAgent as RAGAgent
import httpx

load_dotenv()

app = FastAPI(title="S.O.M.A. API", version="7.1.0")

# WhatsApp Sidecar Config
WHATSAPP_URL = os.getenv("WHATSAPP_URL", "http://localhost:8001")

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

class WhatsAppMessage(BaseModel):
    sender: str
    message: str
    timestamp: Optional[int] = None

import sqlite3
from datetime import datetime

# ... (rest of imports)

class WhatsAppSendRequest(BaseModel):
    to: str
    text: str

class VentureModel(BaseModel):
    id: str
    name: str
    context: str
    production_prompt: str

# Database Helper
def get_db_conn():
    conn = sqlite3.connect(BASE_DIR / "conversations.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Ventures Endpoints
@app.get("/ventures")
async def list_ventures():
    """Lista todos los emprendimientos registrados"""
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ventures ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return {"ventures": [dict(row) for row in rows]}

@app.post("/ventures")
async def upsert_venture(venture: VentureModel):
    """Crea o actualiza un emprendimiento"""
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ventures (id, name, context, production_prompt)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            context=excluded.context,
            production_prompt=excluded.production_prompt
    """, (venture.id, venture.name, venture.context, venture.production_prompt))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Venture {venture.name} guardada"}

@app.get("/ventures/{venture_id}")
async def get_venture(venture_id: str):
    """Obtiene los detalles de un emprendimiento"""
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ventures WHERE id = ?", (venture_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Venture no encontrada")
    return dict(row)

# WhatsApp Endpoints
@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: WhatsAppMessage):
    """Recibe mensajes de WhatsApp desde el Sidecar de Node.js"""
    print(f"📲 WhatsApp Received: {request.message} from {request.sender}")
    
    if not agent:
        return {"status": "error", "message": "Agent not initialized"}
    
    try:
        # Detección dinámica de Venture (Agencia)
        msg_upper = request.message.upper()
        
        # 1. Buscar si hay una Venture vinculada por ID en el mensaje
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ventures")
        all_ids = [row['id'].upper() for row in cursor.fetchall()]
        
        venture_id = "General"
        for vid in all_ids:
            if vid in msg_upper:
                venture_id = vid.lower()
                break
        
        conn.close()
        
        # Limpiamos el ID del sender (soporta WhatsApp y prefijo tg_ de Telegram)
        raw_sender = request.sender
        clean_id = raw_sender.split('@')[0]
        thread_id = f"chat_{clean_id}" # Cambiado de whatsapp_ a chat_ para ser genérico
        
        # Procesar con el agente S.O.M.A. pasando el venture_id real
        result = await agent.chat(request.message, thread_id=thread_id, venture_id=venture_id)
        response_text = result.get("text", "Lo siento, tuve un problema procesando eso.")
        
        # Responder vía Sidecar
        async with httpx.AsyncClient() as client:
            await client.post(f"{WHATSAPP_URL}/send", json={
                "to": request.sender,
                "text": response_text
            })
            
        return {"status": "success", "response": response_text}
    except Exception as e:
        print(f"❌ WhatsApp Webhook Error: {e}")
        return {"status": "error", "detail": str(e)}

@app.post("/whatsapp/send")
async def send_whatsapp_manual(request: WhatsAppSendRequest):
    """Endpoint manual para enviar WhatsApps desde la API/Frontend"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{WHATSAPP_URL}/send", json={
                "to": request.to,
                "text": request.text
            })
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        result = await agent.chat(clean_message, thread_id=request.thread_id)
        
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
