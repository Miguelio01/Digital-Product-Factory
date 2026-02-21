# Guía de Agentes y Orquestación: Digital-Product-Factory

Este proyecto es una factoría inteligente basada en **RAG (Retrieval-Augmented Generation)** diseñada para automatizar la creación, comercialización y promoción de productos digitales en plataformas como Hotmart, Instagram, Facebook y YouTube.

---

## 1. Misión del Proyecto
Transformar documentos de conocimiento y prompts base en campañas de marketing completas y productos digitales listos para la venta, garantizando coherencia estratégica y optimización para cada red social.

---

## 2. Arquitectura del Sistema (Evolución RAG)
El sistema hereda la base del Módulo 5 de Master_IA y se expande con:
- **Knowledge Base:** Repositorio de documentos PDF/DOCX con los "Prompts Maestros" de Miguel.
- **RAG Engine:** Implementación avanzada con LangChain para recuperar el prompt exacto según el canal (IG, YT, Hotmart).
- **Multi-Model Support:** Capacidad de usar Gemini (por su ventana de contexto) y OpenAI.
- **Interface:** Interfaz de chat proactiva para generación de contenido en serie.

---

## 3. Roles de Agentes Especializados (A2A Protocol)

1.  **`rag-architect`:** (Skill: `jeffallan/rag-architect`) Diseña la estructura de la base de datos vectorial y decide la estrategia de embeddings.
2.  **`rag-engineer`:** (Skill: `sickn33/rag-engineer`) Se encarga del chunking semántico de los documentos de prompts para asegurar que el contexto recuperado sea perfecto.
3.  **`prompt-strategist`:** Especialista en convertir los prompts base recuperados en contenido final optimizado para el algoritmo de cada red social.
4.  **`content-implementer`:** Encargado de la lógica de Python (FastAPI/Gradio) para ejecutar el flujo RAG.

---

## 4. Próximos Pasos (Fase 1)
1.  **Auditoría de Ingesta:** Revisar `src/rag/document_processor.py` para asegurar que soporte los formatos de los documentos de Miguel.
2.  **Configuración de Gemini:** Adaptar el agente para que use Gemini como modelo principal opcional.
3.  **Carga de Conocimiento:** Importar los documentos de prompts base al directorio `docs/`.

---

## 5. Fuentes de Verdad
- **Manual del Módulo 5:** `GEMINI.md`
- **Base de Prompts:** Directorio `docs/` (Por completar por Miguel).
