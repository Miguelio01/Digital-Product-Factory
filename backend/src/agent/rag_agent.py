"""
M.I.D.A.S. v6: Multi-session support with LangGraph Checkpoints.
"""
import os
import time
import re
import sqlite3
from typing import List, Optional, Dict, Any, Union, Annotated, TypedDict
from datetime import datetime
from operator import add
from pathlib import Path

from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

import google.generativeai as genai
from ..rag import QdrantVectorStore, RAGRetriever, DocumentProcessor


class AgentState(TypedDict):
    """The state of the agent graph."""
    messages: Annotated[List[BaseMessage], add]
    context: str
    query: str
    standalone_query: str
    image_paths: List[str]


class RAGAgent:
    """Multi-session Consolidated Agent with Persistent Memory (0 COST)."""
    
    MODELS = {
        "expert": "models/gemini-2.5-pro",
        "standard": "models/gemini-2.5-flash",
        "nano": "models/gemini-2.5-flash-lite",
        "research": "models/deep-research-pro-preview-12-2025",
        "image_gen": "models/gemini-2.0-flash-exp-image-generation",
        "image_gen_alt": "models/nano-banana-pro-preview"
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)
        
        self.vector_store = QdrantVectorStore()
        self.retriever = RAGRetriever(self.vector_store)
        self.doc_processor = DocumentProcessor()
        
        self.assets_dir = Path("static/generated_images")
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Checkpointer para persistencia local en SQLite (0 COST)
        # Esto crea un archivo .db para guardar las conversaciones
        self.db_path = "conversations.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.checkpointer = SqliteSaver(self.conn)
        self.agent_executor = self._build_graph()

    def _get_llm(self, model_key: str, temp: float = 0.7):
        return ChatGoogleGenerativeAI(
            google_api_key=SecretStr(self.api_key),
            model=self.MODELS.get(model_key, self.MODELS["standard"]),
            temperature=temp,
            max_output_tokens=8000,
            max_retries=5,
            timeout=120
        )

    def _build_graph(self) -> Any:
        workflow = StateGraph(AgentState)
        
        workflow.add_node("contextualize", self._contextualize_node)
        workflow.add_node("research", self._research_node)
        workflow.add_node("brain", self._brain_node)
        workflow.add_node("render", self._image_gen_node)
        
        workflow.add_edge(START, "contextualize")
        workflow.add_edge("contextualize", "research")
        workflow.add_edge("research", "brain")
        workflow.add_edge("brain", "render")
        workflow.add_edge("render", END)
        
        return workflow.compile(checkpointer=self.checkpointer)

    def _contextualize_node(self, state: AgentState) -> Dict[str, Any]:
        """Use conversation history to create a standalone query for better RAG."""
        if len(state["messages"]) <= 1:
            return {"standalone_query": state["query"]}
            
        contextualize_prompt = """Dado el siguiente historial de conversación y la última pregunta del usuario, 
        que podría hacer referencia al contexto previo, formula una pregunta independiente que se pueda entender 
        sin el historial. NO la respondas, solo reformúlala para que sea una búsqueda efectiva en una base de conocimientos.
        
        Si la pregunta ya es independiente, devuélvela tal cual."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ])
        
        question = state["query"]
        history = state["messages"][:-1]
        
        # Retry logic for contextualization
        for model_key in ["standard", "nano"]:
            for attempt in range(2):
                try:
                    llm = self._get_llm(model_key, temp=0.1)
                    chain = prompt | llm
                    response = chain.invoke({"history": history, "question": question})
                    standalone = response.content.strip()
                    print(f"🧠 Memoria: '{question}' -> '{standalone}'")
                    return {"standalone_query": standalone}
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        print(f"    ⚠️ Cuota agotada en {model_key} (Contextualize). Esperando 6s...")
                        time.sleep(6)
                        continue
                    raise e
        return {"standalone_query": question}

    def _research_node(self, state: AgentState) -> Dict[str, Any]:
        time.sleep(1)
        # Usamos la query contextualizada por la memoria para buscar
        search_query = state.get("standalone_query") or state["query"]
        context = self.retriever.get_context(search_query)
        return {"context": context}

    def _brain_node(self, state: AgentState) -> Dict[str, Any]:
        system_prompt = f"""Eres M.I.D.A.S., un experto Senior en Marketing Digital y Diseño Visual.
        
        CONTEXTO ESTRATÉGICO: {state['context']}
        
        TU MISIÓN:
        1. Analiza profundamente la petición del usuario.
        2. Genera una respuesta estratégica en Markdown de alto impacto.
        3. Si se requiere algo visual, diseña prompts ultra-detallados en bloques ```PROMPT_IMAGEN.
        
        REGLA DE ORO: Tus estrategias deben ser 'Millonarias', como en tus manuales."""

        # Fallback cascade: Pro -> Flash -> Flash Lite (Nano)
        for model_key in ["expert", "standard", "nano"]:
            for attempt in range(2):
                try:
                    llm = self._get_llm(model_key)
                    response = llm.invoke([SystemMessage(content=system_prompt)] + state["messages"])
                    return {"messages": [response]}
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        print(f"    ⚠️ Cuota agotada en {model_key} (Brain). Reintentando en 6s...")
                        time.sleep(6)
                        continue
                    raise e
        return {"messages": [AIMessage(content="He superado todos los límites de cuota gratuitos de Google. Por favor, espera 1 minuto antes de volver a intentar.")]}

    def _image_gen_node(self, state: AgentState) -> Dict[str, Any]:
        last_message = state["messages"][-1].content
        prompts = re.findall(r"```PROMPT_IMAGEN\n(.*?)\n```", last_message, re.DOTALL)
        
        image_paths = []
        if prompts:
            model = genai.GenerativeModel(self.MODELS["image_gen"])
            for i, p_text in enumerate(prompts[:2]):
                try:
                    response = model.generate_content(p_text)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    img_path = self.assets_dir / f"img_{timestamp}_{i}.png"
                    
                    if hasattr(response, 'candidates') and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, 'inline_data'):
                                with open(img_path, "wb") as f:
                                    f.write(part.inline_data.data)
                                image_paths.append(str(img_path))
                except Exception as e:
                    print(f"🎨 Render Error: {e}")
        
        return {"image_paths": image_paths}

    def chat(self, message: str, thread_id: str = "default") -> Dict[str, Any]:
        """Execute chat within a specific thread."""
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {
            "messages": [HumanMessage(content=message)], 
            "query": message, 
            "standalone_query": "", # Inicializamos vacío
            "image_paths": [], 
            "context": ""
        }
        
        result = self.agent_executor.invoke(inputs, config=config)
        
        final_text = result["messages"][-1].content
        return {"text": final_text, "images": result.get("image_paths", [])}

    def get_conversation_history(self, thread_id: str = "default"):
        """Retrieve history for a specific thread."""
        config = {"configurable": {"thread_id": thread_id}}
        state = self.agent_executor.get_state(config)
        if not state or "messages" not in state.values:
            return []
        
        return [{"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} 
                for m in state.values["messages"]]

    def get_knowledge_base_info(self): return {"document_count": self.vector_store.get_document_count()}
    def clear_knowledge_base(self): self.vector_store.clear()
    def add_documents_from_processor(self, docs):
        if not docs: return 0
        self.vector_store.add_documents(docs)
        return len(docs)
