# GEMINI.md

## 🦄 Project Overview

This project is a sophisticated **Retrieval-Augmented Generation (RAG) AI Assistant**. It's built with Python and leverages the power of Large Language Models (LLMs) through the **LangChain** framework and **OpenAI's API**. The assistant is designed to provide answers based on a knowledge base that you create by uploading documents. It features a user-friendly web interface created with **Gradio**.

The core of the application is a `RAGAgent` that can:
- Ingest documents in various formats (PDF, TXT, DOCX) and process them into a searchable vector store.
- Understand and respond to user queries in a conversational manner.
- Retrieve relevant information from the uploaded documents to provide context-aware answers.
- Maintain a conversation history to understand follow-up questions.

The application is containerized using **Docker** and can be easily deployed.

## ✨ Key Features

- **Interactive Chat Interface**: A simple and intuitive chat interface powered by Gradio.
- **Document Upload**: Easily upload your documents (PDF, TXT, DOCX) to build a custom knowledge base.
- **Direct Text Input**: Add text directly to the knowledge base without creating a file.
- **Knowledge Base Search**: Search for relevant information within your documents.
- **Conversation History**: The agent remembers the context of the conversation.
- **Customizable Model**: You can specify the OpenAI model and its temperature.
- **Containerized**: Ready for deployment with Docker.

## 🚀 How to Run Locally

### Prerequisites
- Python 3.10+
- An OpenAI API key

### Steps
1. **Clone the repository.**
2. **Create a `.env` file:**
   - Copy the `.env.example` file to a new file named `.env`.
   - Open the `.env` file and add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     ```
3. **Run the startup script:**
   - Open your terminal and run the following command:
     ```bash
     bash start.sh
     ```
   - This script will:
     - Create a Python virtual environment.
     - Install all the required dependencies.
     - Start the Gradio application.

4. **Access the interface:**
   - Once the application is running, you can access it in your web browser at `http://0.0.0.0:7860`.

## 🐳 How to Run with Docker

### Prerequisites
- Docker installed and running.
- An OpenAI API key.

### Steps
1. **Create a `.env` file** as described in the "How to Run Locally" section.
2. **Build the Docker image:**
   ```bash
   docker build -t rag-ai-assistant .
   ```
3. **Run the Docker container:**
   ```bash
   docker run -p 7860:7860 --env-file .env rag-ai-assistant
   ```
4. **Access the interface:**
   - Open your web browser and navigate to `http://localhost:7860`.

## 📂 Project Structure

```
.
├── app.py                  # Main application entry point
├── Dockerfile              # Docker configuration for containerization
├── requirements.txt        # Python dependencies
├── start.sh                # Startup script for local execution
├── src
│   ├── agent
│   │   └── rag_agent.py      # Core RAG agent implementation
│   ├── interface
│   │   └── gradio_chat.py  # Gradio chat interface
│   └── rag
│       ├── document_processor.py # Document loading and processing
│       └── vector_store.py     # In-memory vector store
└── ...
```

## ⚙️ Customization

You can customize the behavior of the RAG agent by passing command-line arguments when running `app.py`.

- `--host`: The host to run the Gradio interface on (default: `0.0.0.0`).
- `--port`: The port to run the interface on (default: `7860`).
- `--model`: The OpenAI model to use (default: `gpt-5`).
- `--temperature`: The temperature for the model (default: `0.7`).
- `--share`: Create a public Gradio link.
- `--debug`: Enable debug mode.

**Example:**
```bash
python app.py --model gpt-4 --temperature 0.5
```
