"""
🏛️ CORNELIO v4.0: BÚNKER AUTÓNOMO (100% Ollama Local).
Orquestación Maestro-Ejecutor de Costo $0.
"""
import os
import yaml
import asyncio
import re
from typing import List, Optional, Dict, Any, Annotated, TypedDict
from datetime import datetime
from operator import add
from pathlib import Path

from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from google import genai
from google.genai import types
import mss
from PIL import Image
from io import BytesIO

from ..rag import QdrantVectorStore, RAGRetriever

# --- SISTEMA DE EJECUCIÓN S.O.M.A. LOCAL ---

class SOMA_Bunker_Executor:
    def __init__(self):
        self.model = ChatOllama(model="llama3.1:8b", temperature=0.3)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.vs = QdrantVectorStore()
        self.retriever = RAGRetriever(self.vs)

    async def _get_vault_knowledge(self, query: str) -> str:
        """Recupera la sabiduría exacta del baúl vectorial (RAG)."""
        try:
            docs = self.retriever.retrieve(query)
            return "\n---\n".join([d.page_content for d in docs])
        except:
            return "No se pudo recuperar conocimiento específico del baúl."

    async def run_skill(self, skill: str, task: str, context: str = "") -> str:
        """Ejecuta una personalidad de S.O.M.A. potenciada por RAG local."""
        print(f"⚙️ S.O.M.A. consultando el Baúl para el Skill: {skill}...")
        
        # PASO MAESTRO: Recuperamos conocimiento específico antes de actuar
        vault_knowledge = await self._get_vault_knowledge(f"Prompt Millonario {skill} {task}")
        
        if skill == "watcher": return await self._run_watcher(task)
        if skill == "design": return await self._run_designer(task, context, vault_knowledge)
        if skill == "avatar": return await self._run_avatar_research(task, context, vault_knowledge)
        if skill == "viability": return await self._run_viability_check(task, context, vault_knowledge)
        if skill == "naming": return await self._run_naming_expert(task, context, vault_knowledge)
        
        prompt = f"""Actúa como S.O.M.A. especializado en {skill}.
SABIDURÍA DEL BAÚL (RAG): {vault_knowledge}
CONTEXTO ESTRATÉGICO: {context}
TAREA: {task}
Usa la sabiduría del baúl para entregar un resultado de élite:"""
        
        response = await self.model.ainvoke([HumanMessage(content=prompt)])
        return response.content

    async def _run_avatar_research(self, task: str, context: str, vault: str) -> str:
        """Investigación ICP potenciada por RAG."""
        prompt = f"""Usa este PROMPT MAESTRO recuperado del baúl: {vault}
Aclara y ejecuta la investigación para: {task}
Contexto del Negocio: {context}"""
        res = await self.model.ainvoke([HumanMessage(content=prompt)])
        return res.content

    async def _run_viability_check(self, task: str, context: str, vault: str) -> str:
        """Validación de Viabilidad potenciada por RAG."""
        prompt = f"""Usa este PROMPT MAESTRO recuperado del baúl: {vault}
Valida la viabilidad de: {task}
Contexto: {context}"""
        res = await self.model.ainvoke([HumanMessage(content=prompt)])
        return res.content

    async def _run_naming_expert(self, task: str, context: str, vault: str) -> str:
        """Naming de Élite potenciado por RAG."""
        prompt = f"""Usa este PROMPT MAESTRO recuperado del baúl: {vault}
Crea nombres memorables para: {task}
Contexto: {context}"""
        res = await self.model.ainvoke([HumanMessage(content=prompt)])
        return res.content

    async def _run_designer(self, task: str, context: str, vault: str) -> str:
        """S.O.M.A. Designer con sabiduría de Director de Arte del Baúl."""
        try:
            translation_prompt = f"""Director de Arte Estratégico.
Usa esta SABIDURÍA DE DISEÑO del baúl: {vault}
Traduce la petición: {task}
Contexto: {context}
Genera el Prompt Maestro para Nano Banana en inglés:"""
            
            tech_prompt_res = await self.model.ainvoke([HumanMessage(content=translation_prompt)])
            tech_prompt = tech_prompt_res.content.strip()
            
            client = genai.Client(api_key=self.api_key)
            client.models.generate_content(model="models/gemini-2.5-flash-image", contents=tech_prompt)
            
            return f"✅ S.O.M.A. Designer: Activo visual generado usando sabiduría del baúl.\nPROMPT: {tech_prompt}"
        except Exception as e:
            return f"❌ S.O.M.A. Designer Error: {e}"

    async def _run_watcher(self, topic: str) -> str:
        """Watcher (Visión) - Única herramienta que intenta usar nube como fallback."""
        try:
            with mss.mss() as sct:
                img = Image.frombytes("RGB", sct.grab(sct.monitors[1]).size, sct.grab(sct.monitors[1]).bgra, "raw", "BGRX")
                buffered = BytesIO()
                img.save(buffered, format="JPEG", quality=80)
                
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model="models/gemini-2.0-flash", # Intentamos Flash para visión
                    contents=[types.Part.from_bytes(data=buffered.getvalue(), mime_type="image/jpeg"), 
                              f"Extrae conocimiento de CODIGOMILLION sobre: {topic}"]
                )
                
                vs = QdrantVectorStore()
                from langchain_core.documents import Document
                vs.add_documents([Document(page_content=response.text, metadata={"source": "CODIGOMILLION", "topic": topic})])
                return f"✅ Conocimiento de '{topic}' inyectado al baúl."
        except Exception as e:
            return f"❌ Watcher Error (Probablemente cuota/API): {e}. S.O.M.A. recomienda usar entrada de texto manual por ahora."

# --- AGENTE CORNELIO (EL ALMA DEL BÚNKER) ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add]
    venture_context: str

class CornelioAgent:
    def __init__(self):
        # CORNELIO Local (Gemma 3 4B - El ADN de Gemini en tu Mac)
        self.model = ChatOllama(model="gemma3:4b", temperature=0.2)
        self.executor = SOMA_Bunker_Executor()
        self.checkpointer = InMemorySaver()
        self.agent_executor = self._build_graph()
        self.venture_config = self._load_venture_config()

    def _load_venture_config(self) -> str:
        config_path = Path("ventures/pilot_venture/venture_config.yaml")
        if config_path.exists():
            with open(config_path, "r") as f:
                return f"ESTADO DEL NEGOCIO:\n{yaml.dump(yaml.safe_load(f))}"
        return "Iniciando nuevo proyecto."

    def _build_graph(self) -> Any:
        workflow = StateGraph(AgentState)
        workflow.add_node("cornelio", self._cornelio_node)
        workflow.add_node("soma", self._soma_node)
        workflow.add_edge(START, "cornelio")
        
        # Lógica de ruteo por texto (Commands)
        def route_cornelio(state: AgentState):
            last_msg = state["messages"][-1].content
            if "[EJECUTAR:" in last_msg:
                return "soma"
            return "end"

        workflow.add_conditional_edges("cornelio", route_cornelio, {"soma": "soma", "end": END})
        workflow.add_edge("soma", "cornelio")
        return workflow.compile(checkpointer=self.checkpointer)

    async def _cornelio_node(self, state: AgentState) -> Dict[str, Any]:
        system_msg = f"""Eres CORNELIO, CEO y Orquestador Mayor del Búnker Autónomo.
{state['venture_context']}

MAPA DE DELEGACIÓN OBLIGATORIO PARA S.O.M.A.:
1. [EJECUTAR: avatar | TAREA: ...] -> Uso exclusivo para investigar al Cliente Ideal (ICP), miedos y deseos.
2. [EJECUTAR: naming | TAREA: ...] -> Uso exclusivo para crear nombres de productos, marcas o dominios.
3. [EJECUTAR: viability | TAREA: ...] -> Uso exclusivo para validar si una idea es rentable.
4. [EJECUTAR: copy | TAREA: ...] -> Para redacción de anuncios, correos, guiones y cartas de venta.
5. [EJECUTAR: design | TAREA: ...] -> Para creación de imágenes con Nano Banana y diseño visual.
6. [EJECUTAR: watcher | TAREA: ...] -> Para capturar y aprender del curso CODIGOMILLION en pantalla.

DIRECTRICES:
- No mezcles departamentos. Cada tarea debe ir a su Skill correspondiente.
- Tu enfoque es siempre el ROI y la Estrategia Millonaria.
- Si no necesitas ejecutar, simplemente responde como el estratega que eres.
"""
        response = await self.model.ainvoke([SystemMessage(content=system_msg)] + state["messages"])
        return {"messages": [response]}

    async def _soma_node(self, state: AgentState) -> Dict[str, Any]:
        last_msg = state["messages"][-1].content
        # Regex para extraer el comando de Cornelio
        match = re.search(r"\[EJECUTAR:\s*(.*?)\s*\|\s*TAREA:\s*(.*?)\]", last_msg)
        
        if match:
            skill = match.group(1).strip().lower()
            task = match.group(2).strip()
            result = await self.executor.run_skill(skill, task, state['venture_context'])
            return {"messages": [AIMessage(content=f"⚙️ S.O.M.A. Reporte de Ejecución:\n{result}")]}
        
        return {"messages": [AIMessage(content="❌ S.O.M.A.: Comando de ejecución no detectado correctamente.")]}

    async def chat(self, message: str, thread_id: str = "default") -> Dict[str, Any]:
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {"messages": [HumanMessage(content=message)], "venture_context": self.venture_config}
        result = await self.agent_executor.ainvoke(inputs, config=config)
        return {"text": result["messages"][-1].content}
