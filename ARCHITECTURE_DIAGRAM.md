# 📊 Arquitectura de Flujo: M.I.D.A.S. Multi-Venture Orchestrator

Este diagrama detalla cómo interactúas con el sistema y cómo M.I.D.A.S. orquesta sus procesos internos de forma autónoma.

```mermaid
sequenceDiagram
    participant U as 👤 Miguel (Usuario)
    participant M as 🧠 M.I.D.A.S. (Orchestrator)
    participant S as 📜 SOUL & Ventures (Memoria)
    participant V as 📚 BD Vectorial (Prompts Millonarios)
    participant R as 🔍 Sub-Agente Research (Deep)
    participant D as 🎨 Sub-Agente Design (Visual)
    participant C as ✍️ Sub-Agente Copy (Strategy)

    U->>M: Envía Petición (Chat/Voz)
    M->>S: Consulta Contexto del Emprendimiento
    S-->>M: Devuelve: Reglas y Tono

    Note over M: "Extrayendo Inteligencia Experta..."
    M->>V: Busca Prompts Ganadores y Manuales
    V-->>M: Devuelve: Estructuras IR y Plantillas Maestras

    rect rgb(240, 240, 240)
        Note right of M: Ejecución Guiada por Conocimiento
        M->>R: Deep Research (Usando manuales recuperados)
        R-->>M: Reporte Estratégico

        M->>C: Genera Copy (Usando Plantillas Millonarias)
        C-->>M: Guiones y Ofertas Irresistibles

        M->>D: Genera Diseño (Usando Prompts de Imagen Expertos)
        D-->>M: Conceptos Visuales de Alto Impacto
    end

    M->>M: Autocrítica (Soul Check)
    M->>U: Entrega Resultado Final (Estrategia Completa)
```

## 📂 Desglose de Procesos

1.  **Identificación de Venture:** M.I.D.A.S. detecta automáticamente si estás trabajando en el negocio de "Inversiones", "Inmobiliario" o "Marketing" para no mezclar estrategias.
2.  **Orquestación de Sub-Agentes:** El Cerebro Central no hace el trabajo pesado; delega en las **Skills** especializadas que tienen sus propios prompts maestros.
3.  **Persistencia del Soul:** Antes de entregarte la respuesta, M.I.D.A.S. verifica si el tono y la ética coinciden con lo definido en tu archivo `SOUL.md`.
4.  **Memoria Evolutiva:** El sistema anota qué te gustó y qué no en el archivo de memoria del emprendimiento para ser más certero en la próxima sesión.
```
