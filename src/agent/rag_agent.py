"""
Advanced Multi-Modal AI Agent with Dynamic Model Selection, RAG, and Image Generation.
"""
import os
import time
import re
from typing import List, Optional, Dict, Any, Union, Annotated, TypedDict
from datetime import datetime
from operator import add
from pathlib import Path

from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END

# Import for real image generation
import google.generativeai as genai

from ..rag import QdrantVectorStore, RAGRetriever, DocumentProcessor


class AgentState(TypedDict):
    """The state of the agent graph including multimedia assets."""
    messages: Annotated[List[BaseMessage], add]
    context: str
    query: str
    current_step: str
    selected_model: str
    image_paths: List[str] # Almacena las rutas de las imágenes generadas


class RAGAgent:
    """Advanced Multi-Modal Agent (M.I.D.A.S.)."""
    
    MODELS = {
        "supreme": "models/gemini-3-pro-preview",
        "expert": "models/gemini-2.5-pro",
        "research": "models/deep-research-pro-preview-12-2025",
        "standard": "models/gemini-2.5-flash",
        "future_flash": "models/gemini-3-flash-preview",
        "legacy": "models/gemini-2.0-flash",
        "lite": "models/gemini-2.5-flash-lite",
        "nano": "models/nano-banana-pro-preview",
        "image_gen": "models/gemini-2.0-flash-exp-image-generation"
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 12000
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required (GOOGLE_API_KEY)")
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Configure Google SDK for Image Generation
        genai.configure(api_key=self.api_key)
        
        # Initialize RAG components
        self.vector_store = QdrantVectorStore()
        self.retriever = RAGRetriever(self.vector_store)
        self.doc_processor = DocumentProcessor()
        
        # Storage
        self._llm_instances = {}
        self.chat_history: List[BaseMessage] = []
        
        # Assets directory
        self.assets_dir = Path("static/generated_images")
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Build Graph
        self.agent_executor = self._build_graph()

    def _get_llm(self, model_key: str) -> ChatGoogleGenerativeAI:
        model_name = self.MODELS.get(model_key, self.MODELS["standard"])
        if model_name not in self._llm_instances:
            self._llm_instances[model_name] = ChatGoogleGenerativeAI(
                google_api_key=SecretStr(self.api_key),
                model=model_name,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                max_retries=3,
                timeout=120
            )
        return self._llm_instances[model_name]

    def _build_graph(self) -> Any:
        workflow = StateGraph(AgentState)
        
        workflow.add_node("router", self._router_node)
        workflow.add_node("research", self._research_node)
        workflow.add_node("filter", self._filter_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("image_gen", self._image_gen_node) # Nuevo nodo visual
        
        workflow.add_edge(START, "router")
        workflow.add_edge("router", "research")
        workflow.add_edge("research", "filter")
        workflow.add_edge("filter", "generate")
        workflow.add_edge("generate", "image_gen") # De texto a imagen
        workflow.add_edge("image_gen", END)
        
        return workflow.compile()

    def _router_node(self, state: AgentState) -> Dict[str, Any]:
        query = state["query"].lower()
        multimedia = ["imagen", "video", "logo", "diseño", "banner", "thumbnail", "propuesta visual"]
        
        if any(word in query for word in multimedia):
            selected = "nano"
        elif any(word in query for word in ["analiza", "estrategia", "profundo"]):
            selected = "expert"
        else:
            selected = "standard"
            
        return {"selected_model": selected, "image_paths": []}

    def _research_node(self, state: AgentState) -> Dict[str, Any]:
        context = self.retriever.get_context(state["query"])
        return {"context": context}

    def _filter_node(self, state: AgentState) -> Dict[str, Any]:
        context = state.get("context", "")
        if not context or len(context.strip()) < 50:
            return {"context": ""}
        return {"context": context}

    def _generate_node(self, state: AgentState) -> Dict[str, Any]:
        model_key = state.get("selected_model", "standard")
        context = state.get("context", "")
        
        system_prompt = f"""Eres M.I.D.A.S., experto Senior en Marketing Digital.
        
        CONTEXTO ESTRATÉGICO:
        {context}
        
        INSTRUCCIONES CLAVE:
        1. Responde en Markdown.
        2. Si el usuario pide contenido visual, incluye SIEMPRE un bloque de código marcado como 'PROMPT_IMAGEN' con la descripción detallada.
           Ejemplo: 
           ```PROMPT_IMAGEN
           Un logo minimalista para Raíz del Huerto, verde oliva, estilo premium.
           ```
        3. Estás usando el modelo: {self.MODELS.get(model_key)}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])

        fallback_order = [model_key, "supreme", "expert", "standard", "legacy", "nano"]
        fallback_order = list(dict.fromkeys(fallback_order))

        for current_key in fallback_order:
            try:
                llm = self._get_llm(current_key)
                chain = prompt | llm
                response = chain.invoke({"messages": state["messages"]})
                return {"messages": [response]}
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    time.sleep(2)
                    continue
                raise e
        return {"messages": [AIMessage(content="Lo siento, M.I.D.A.S. está experimentando alta demanda. Inténtalo en un momento.")]}

    def _image_gen_node(self, state: AgentState) -> Dict[str, Any]:
        """Node to extract image prompts and generate actual images."""
        last_message = state["messages"][-1].content
        # Buscar bloques de código 'PROMPT_IMAGEN'
        prompts = re.findall(r"```PROMPT_IMAGEN\n(.*?)\n```", last_message, re.DOTALL)
        
        if not prompts:
            # Búsqueda secundaria si no usó el bloque exacto
            prompts = re.findall(r"Prompt para imagen.*?: (.*)", last_message, re.IGNORECASE)

        image_paths = []
        if prompts:
            print(f"🎨 M.I.D.A.S. detectó {len(prompts)} prompts de imagen. Generando...")
            model = genai.GenerativeModel(self.MODELS["image_gen"])
            
            for i, p_text in enumerate(prompts[:2]): # Limitamos a 2 imágenes por respuesta para no saturar
                try:
                    # Llamada a la API de generación de imágenes de Google
                    # Nota: Esto asume que el modelo soporta generate_content con prompt de texto para imagen
                    # Si la API requiere un método específico, lo ajustaremos.
                    response = model.generate_content(p_text)
                    
                    # Guardar la imagen (esto depende de cómo devuelva los bytes el modelo experimental)
                    # Por ahora simulamos la ruta, ya que el modelo experimental puede devolver bytes en parts
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    img_path = self.assets_dir / f"img_{timestamp}_{i}.png"
                    
                    # Lógica de extracción de bytes (placeholder según SDK actual)
                    if hasattr(response, 'candidates') and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, 'inline_data'):
                                with open(img_path, "wb") as f:
                                    f.write(part.inline_data.data)
                                image_paths.append(str(img_path))
                except Exception as e:
                    print(f"❌ Error generando imagen {i}: {e}")
        
        return {"image_paths": image_paths}

    def chat(self, message: str) -> Dict[str, Any]:
        """Execute the graph and return text + assets."""
        inputs = {
            "messages": [HumanMessage(content=message)],
            "query": message,
            "image_paths": []
        }
        
        result = self.agent_executor.invoke(inputs)
        final_text = result["messages"][-1].content
        final_images = result.get("image_paths", [])
        
        self.chat_history.append(HumanMessage(content=message))
        self.chat_history.append(AIMessage(content=final_text))
        
        return {
            "text": final_text,
            "images": final_images
        }

    # Compatibilidad con UI
    def get_knowledge_base_info(self):
        return {"document_count": self.vector_store.get_document_count()}
    def clear_knowledge_base(self):
        self.vector_store.clear()
    def add_documents_from_processor(self, docs):
        self.vector_store.add_documents(docs)
    def clear_conversation_history(self):
        self.chat_history.clear()
    def get_conversation_history(self):
        return [{"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} for m in self.chat_history]