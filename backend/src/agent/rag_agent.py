"""
🏛️ CORNELIO v5.8: AGENCIA CON MEMORIA ASÍNCRONA CORREGIDA.
Uso de context manager para persistencia SQLite.
"""
import os
import sqlite3
import asyncio
from typing import List, Optional, Dict, Any, Annotated, TypedDict
from operator import add

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ..rag.vector_store import QdrantVectorStore, RAGRetriever
from .tools import FILES_TOOLS, SOCIAL_TOOLS, MAIL_DEPARTMENT

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add]
    venture_id: Optional[str]

class SOMA_Specialist:
    def __init__(self, name: str, tools: list, model_name: str = "llama3.1:8b"):
        self.name = name
        self.model = ChatOllama(model=model_name, temperature=0.1).bind_tools(tools)
        self.tools = tools

    async def execute(self, task: str) -> str:
        messages = [HumanMessage(content=f"Actúa como {self.name}. TAREA: {task}")]
        for _ in range(3):
            try:
                resp = await self.model.ainvoke(messages)
                messages.append(resp)
                if not resp.tool_calls: break
                for tc in resp.tool_calls:
                    t_func = next((t for t in self.tools if t.name == tc["name"]), None)
                    if t_func:
                        res = await t_func.ainvoke(tc["args"])
                        messages.append(AIMessage(content=str(res)))
            except Exception as e:
                return f"Error en especialista {self.name}: {str(e)}"
        return messages[-1].content

class CornelioAgent:
    def __init__(self):
        print("⚡ CORNELIO: Agencia con Memoria SQLite (Async Safe)")
        self.model = ChatOllama(model="llama3.1:8b", temperature=0.2)
        
        self.vector_store = QdrantVectorStore()
        self.retriever = RAGRetriever(self.vector_store)
        
        self.system_expert = SOMA_Specialist("S.O.M.A. System", FILES_TOOLS)
        self.social_expert = SOMA_Specialist("S.O.M.A. Social", SOCIAL_TOOLS)
        self.mail_expert = SOMA_Specialist("S.O.M.A. Mail", MAIL_DEPARTMENT)
        
        self.db_path = "conversations.db"

    def _get_venture_data(self, venture_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ventures WHERE id = ?", (venture_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except:
            return None

    def _build_graph(self, checkpointer):
        workflow = StateGraph(AgentState)
        workflow.add_node("cornelio", self._cornelio_node)
        workflow.add_node("soma_system", self._system_node)
        workflow.add_node("soma_social", self._social_node)
        workflow.add_node("soma_mail", self._mail_node)
        workflow.add_edge(START, "cornelio")

        def route(state):
            msg = state["messages"][-1].content.upper()
            if "DELEGAR: SYSTEM" in msg: return "system"
            if "DELEGAR: SOCIAL" in msg: return "social"
            if "DELEGAR: MAIL" in msg: return "mail"
            return "end"

        workflow.add_conditional_edges("cornelio", route, {
            "system": "soma_system", "social": "soma_social", "mail": "soma_mail", "end": END
        })
        workflow.add_edge("soma_system", "cornelio")
        workflow.add_edge("soma_social", "cornelio")
        workflow.add_edge("soma_mail", "cornelio")
        
        # El checkpointer se pasa al compilar
        return workflow.compile(checkpointer=checkpointer)

    async def _cornelio_node(self, state):
        venture_id = state.get("venture_id", "General")
        v_data = self._get_venture_data(venture_id)
        
        context = v_data["context"] if v_data else "Agencia de automatización general."
        rules = v_data["production_prompt"] if v_data else "Sé profesional y conciso."
        
        user_query = state["messages"][-1].content
        rag_knowledge = self.retriever.get_context(user_query, venture_id=venture_id)
        
        sys = f"""Eres CORNELIO, Director de la Agencia. 
        ESTÁS GESTIONANDO: {venture_id}
        ADN DEL EMPRENDIMIENTO:
        {context}
        
        HILO CONDUCTOR (REGLAS):
        {rules}
        
        CONOCIMIENTO RECUPERADO (RAG):
        {rag_knowledge}
        
        Instrucciones: Responde por WhatsApp basándote en el ADN y el CONOCIMIENTO RECUPERADO.
        Delega tareas técnicas a S.O.M.A. usando los comandos [DELEGAR: ...]
        """
        print(f"🧠 Cornelio analizando RAG para {venture_id}...")
        resp = await self.model.ainvoke([SystemMessage(content=sys)] + state["messages"])
        return {"messages": [resp]}

    async def _system_node(self, state):
        res = await self.system_expert.execute(state["messages"][-1].content)
        return {"messages": [AIMessage(content=f"🏢 S.O.M.A. System Reporte:\n{res}")]}

    async def _social_node(self, state):
        res = await self.social_expert.execute(state["messages"][-1].content)
        return {"messages": [AIMessage(content=f"🌐 S.O.M.A. Social Reporte:\n{res}")]}

    async def _mail_node(self, state):
        res = await self.mail_expert.execute(state["messages"][-1].content)
        return {"messages": [AIMessage(content=f"📧 S.O.M.A. Mail Reporte:\n{res}")]}

    async def chat(self, message: str, thread_id: str = "default", venture_id: str = "General"):
        # Usamos el administrador de contexto correctamente
        async with AsyncSqliteSaver.from_conn_string(self.db_path) as memory:
            graph = self._build_graph(memory)
            config = {"configurable": {"thread_id": thread_id}}
            res = await graph.ainvoke({"messages": [HumanMessage(content=message)], "venture_id": venture_id}, config=config)
            return {"text": res["messages"][-1].content}
