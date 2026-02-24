# 🚀 M.I.D.A.S. v2.0: Hoja de Ruta del Agente Autónomo

Este documento define la evolución de M.I.D.A.S. desde un sistema RAG estático hacia un **Agente de IA Autónomo Local-First**, basado en los paradigmas de **OpenClaw**, **Soul** y **OpenSpec**.

---

## 🏗️ 1. Arquitectura del Sistema (Paradigma Evolucionado)

### A. Capa de Identidad (CEO ORCHESTRATOR)
M.I.D.A.S. actuará como el Director de Orquesta de múltiples negocios.
- **`SOUL.md`:** Identidad central de M.I.D.A.S. (Socio de élite y estratega jefe).
- **`VENTURES_MANAGER`:** Sistema para conmutar entre diferentes emprendimientos.
- **Venture Workspaces:** Cada negocio en `/ventures/[nombre_negocio]/` con su propio `VENTURE_CONTEXT.md`, productos y base de conocimientos.

### B. Capa de Habilidades (MODULAR SKILLS) - Inspirado en OpenClaw
En lugar de funciones fijas, usaremos **AgentSkills** que el CEO invoca según el negocio.
- `/backend/skills/`: Carpeta que contiene módulos autónomos reutilizables.
- **Skills de Nicho:** Estrategias adaptadas a cada emprendimiento (Inversiones, Marketing, etc.).
- **Skills de Despliegue:** (Futuro) Automatización de pautas y posts por cada negocio.

### C. Capa de Decisión (THE MULTI-VENTURE LOOP)
1. **IDENTIFY:** Detecta el "Negocio" activo mediante el `thread_id` o metadatos.
2. **CONTEXTUALIZE:** Carga las reglas específicas y el catálogo de ese emprendimiento.
3. **RESEARCH:** Realiza búsquedas (RAG) filtrando SOLO los manuales del negocio actual.
4. **THINK & ACT:** El modelo Líder coordina las Skills para cumplir el objetivo del negocio.

---

## 📅 2. Fases de Implementación (Roadmap)

### Fase 1: Cimentación (Identidad y Estándar) - **ESTADO: INICIANDO**
- [ ] Crear estructura `SOUL.md` e `IDENTITY.md`.
- [ ] Implementar el "Prompt de Identidad" dinámico en `rag_agent.py`.
- [ ] Adoptar **OpenSpec** para definir las tareas de M.I.D.A.S. de forma declarativa.

### Fase 2: Modularización (Skill Platform)
- [ ] Refactorizar la lógica actual (RAG, Voz, Imagen) en carpetas independientes de `Skills`.
- [ ] Crear el "Skill Registry" para que M.I.D.A.S. sepa qué herramientas tiene "en su cinturón".

### Fase 3: Autonomía y Bucle (Brain Upgrade)
- [ ] Actualizar el Grafo de LangGraph para permitir **Re-planificación**.
- [ ] Implementar el "Monólogo Interno" (Thought process) visible en los logs.
- [ ] Integrar el modelo de **Deep Research** como la Skill de investigación por defecto.

### Fase 4: Multicanalidad (Despliegue)
- [ ] Conexión con **WhatsApp/Telegram** (vía Webhooks locales).
- [ ] Integración de **Canvas Interactivo** para previsualizar landing pages/anuncios.

---

## 🎯 3. Objetivo Final
Convertir a M.I.D.A.S. en un socio que:
1. **No espera instrucciones paso a paso:** Recibe una meta (ej: "Lanza el curso de inversiones") y ejecuta el plan.
2. **Aprende de ti:** Su `MEMORY.md` crece con cada interacción, volviéndose más "tuyo" cada día.
3. **Es $0 Cost:** Maximiza el uso de modelos gratuitos de Gemini y persistencia local (SQLite/Qdrant).

---
*Documento creado por J.A.R.V.I.S. (Orquestador Principal) para Miguel.*
