# 🚀 Instrucciones de Montaje en Local - Digital-Product-Factory

Este documento detalla los pasos para poner en marcha tanto el **Backend (FastAPI)** como el **Frontend (Next.js 16)** en tu entorno local.

---

## 🛠️ Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:
- **Python 3.11** o superior.
- **Node.js 18** o superior.
- **pnpm** (recomendado para el frontend).
- **Git**.

---

## 📂 1. Configuración del Backend (FastAPI)

El backend gestiona la lógica de RAG (Retrieval-Augmented Generation), el procesamiento de documentos y la integración con Gemini/OpenAI.

1. **Navega a la carpeta del backend:**
   ```bash
   cd backend
   ```

2. **Crea un entorno virtual:**
   ```bash
   python -m venv venv
   ```

3. **Activa el entorno virtual:**
   - **macOS/Linux:**
     ```bash
     cd
     ```
   - **Windows:**
     ```bash
     .\venv\Scripts\activate
     ```

4. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configura las variables de entorno:**
   Verifica que el archivo `.env` en `backend/` tenga las credenciales correctas (Google API Key, Qdrant, etc.). Si no existe, créalo basándote en `.env.example`.

6. **Inicia el servidor de desarrollo:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   *El backend estará disponible en `http://localhost:8000`.*

---

## 💻 2. Configuración del Frontend (Next.js 16)

El frontend es una aplicación moderna construida con Next.js 16, Tailwind CSS y Framer Motion.

1. **Navega a la carpeta del frontend:**
   ```bash
   cd frontend
   ```

2. **Instala las dependencias:**
   ```bash
   pnpm install
   ```

3. **Configura las variables de entorno:**
   Asegúrate de que el archivo `.env.local` contenga:
   ```env
   NEXTAUTH_URL=http://localhost:3000
   NEXT_PUBLIC_API_URL=http://localhost:8000
   # Añade tus credenciales de Google Auth si es necesario
   ```

4. **Inicia el servidor de desarrollo:**
   ```bash
   pnpm dev
   ```
   *El frontend estará disponible en `http://localhost:3000`.*

---

## 🤖 3. Opción Alternativa: Interfaz Gradio

Si prefieres usar la interfaz de **Gradio** (más sencilla para pruebas rápidas de IA), puedes ejecutarla desde la raíz del proyecto:

1. **Regresa a la raíz:**
   ```bash
   cd ..
   ```

2. **Activa el entorno virtual principal:**
   ```bash
   source venv/bin/activate
   ```

3. **Instala las dependencias de la raíz:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Lanza Gradio:**
   ```bash
   python app.py
   ```
   *Se abrirá automáticamente en tu navegador o mostrará una URL local.*

---

## 📝 Notas Adicionales

- **Ingesta de Conocimiento:** Para cargar nuevos documentos a la base de datos vectorial, puedes usar los endpoints `/ingest/files` del backend o ejecutar el script `ingest_knowledge.py` en la raíz.
- **Modelos:** Por defecto, el sistema está configurado para usar `gemini-2.0-flash`. Puedes cambiarlo en el `.env` del backend.

---
*J.A.R.V.I.S. - Orchestrating your Digital Factory*
