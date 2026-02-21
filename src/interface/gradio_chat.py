"""
Gradio interface for the ChatGPT-like AI agent.
"""
import os
from typing import List, Tuple, Dict
import gradio as gr

from ..agent import RAGAgent
from ..rag import DocumentProcessor
from .voice_service import VoiceService


class ChatInterface:
    """Gradio-based chat interface with voice capabilities for the RAG agent."""
    
    def __init__(self, agent: RAGAgent, title: str = "AI Assistant with RAG"):
        self.agent = agent
        self.title = title
        self.doc_processor = DocumentProcessor()
        self.voice_service = VoiceService()
        
    def process_uploaded_files(self, files: List[str]) -> str:
        """Process uploaded files and add them to the knowledge base."""
        if not files:
            return "No files uploaded."
        
        total_docs = 0
        processed_files = []
        
        for file_path in files:
            try:
                # Process the document
                documents = self.doc_processor.load_document(file_path)
                
                # Add to knowledge base
                self.agent.add_documents_from_processor(documents)
                
                total_docs += len(documents)
                processed_files.append(os.path.basename(file_path))
                
            except Exception as e:
                return f"Error processing {os.path.basename(file_path)}: {str(e)}"
        
        files_list = ", ".join(processed_files)
        return f"Successfully processed {len(processed_files)} file(s): {files_list}. Added {total_docs} document chunks to knowledge base."
    
    def add_text_to_knowledge_base(self, text: str) -> str:
        """Add text directly to the knowledge base."""
        if not text.strip():
            return "No text provided."
        
        try:
            documents = self.doc_processor.process_text_input(text, "manual_input")
            self.agent.add_documents_from_processor(documents)
            return f"Added text to knowledge base ({len(documents)} chunks)."
        except Exception as e:
            return f"Error adding text: {str(e)}"
    
    def clear_knowledge_base(self) -> str:
        """Clear the knowledge base."""
        self.agent.clear_knowledge_base()
        return "Knowledge base cleared."
    
    def clear_chat_history(self) -> Tuple[List[dict], str]:
        """Clear the chat history."""
        self.agent.clear_conversation_history()
        return [], "Chat history cleared."
    
    def get_knowledge_base_status(self) -> str:
        """Get the current status of the knowledge base."""
        info = self.agent.get_knowledge_base_info()
        return f"Documents in knowledge base: {info['document_count']}"
    
    def chat_response(self, message: str, history: List[dict]) -> Tuple[List[dict], str, List[str]]:
        """Generate chat response with assets."""
        if not message.strip():
            return history, "", []
        
        try:
            # El agente ahora devuelve un dict con 'text' e 'images'
            result = self.agent.chat(message)
            
            # Extraer contenido
            if isinstance(result, dict):
                response_text = result.get("text", "")
                generated_images = result.get("images", [])
            else:
                response_text = str(result)
                generated_images = []
            
            # Actualizar historial
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response_text})
            
            return history, "", generated_images
            
        except Exception as e:
            error_response = f"Error: {str(e)}"
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_response})
            return history, "", []
    
    def search_documents(self, query: str) -> str:
        """Search documents in the knowledge base."""
        if not query.strip():
            return "Please enter a search query."
        
        try:
            results = self.agent.search_documents(query, k=3)
            
            if not results:
                return "No relevant documents found."
            
            output = f"Found {len(results)} relevant document(s):\n\n"
            
            for i, result in enumerate(results, 1):
                metadata = result["metadata"]
                source = metadata.get("source", "Unknown")
                output += f"**Result {i}** (Source: {os.path.basename(source)})\n"
                output += f"{result['preview']}\n\n"
            
            return output
            
        except Exception as e:
            return f"Error searching documents: {str(e)}"
    
    def voice_chat_response(self, audio_path: str, history: List[dict]) -> Tuple[List[dict], str, str]:
        """Handle voice input, generate text response, and then audio output."""
        if not audio_path:
            return history, "", None
            
        try:
            # 1. Escuchar (STT)
            text_query = self.voice_service.transcribe(audio_path)
            
            # 2. Pensar (Agent Chat)
            response_text = self.agent.chat(text_query)
            
            # 3. Hablar (TTS)
            output_audio = self.voice_service.speak(response_text)
            
            # Update history
            history.append({"role": "user", "content": text_query})
            history.append({"role": "assistant", "content": response_text})
            
            return history, "", output_audio
            
        except Exception as e:
            return history, f"Error en voz: {str(e)}", None

    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface with voice support."""
        with gr.Blocks(title=self.title) as interface:
            gr.Markdown(f"# {self.title}")
            
            with gr.Tab("💬 Chat"):
                with gr.Row():
                    with gr.Column(scale=4):
                        chatbot = gr.Chatbot(
                            label="M.I.D.A.S. Intelligence",
                            height=500
                        )
                        
                        # Nueva Galería para imágenes generadas
                        image_gallery = gr.Gallery(
                            label="Activos Visuales Generados",
                            show_label=True,
                            columns=[2],
                            rows=[1],
                            object_fit="contain",
                            height="auto"
                        )
                        
                        with gr.Row():
                            msg = gr.Textbox(
                                placeholder="Escribe tu mensaje aquí (puedes usar el dictado de tu Mac)...",
                                label="Tu Mensaje",
                                scale=4
                            )
                            submit_btn = gr.Button("Enviar", variant="primary", scale=1)
                        
                        audio_output = gr.Audio(label="Voz de M.I.D.A.S.", autoplay=True)
                        clear_btn = gr.Button("Limpiar Chat")
                    
                    with gr.Column(scale=1):
                        status_display = gr.Textbox(
                            label="Knowledge Base Status",
                            value=self.get_knowledge_base_status(),
                            interactive=False
                        )
                        
                        refresh_status_btn = gr.Button("Refresh Status")
            
            with gr.Tab("📄 Document Management"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Upload Documents")
                        file_upload = gr.File(
                            label="Upload Files (PDF, TXT, DOCX)",
                            file_count="multiple",
                            file_types=[".pdf", ".txt", ".docx"],
                            elem_classes=["upload-area"]
                        )
                        upload_btn = gr.Button("Process Files", variant="primary")
                        upload_status = gr.Textbox(label="Upload Status", interactive=False)
                        
                        gr.Markdown("### Add Text Directly")
                        text_input = gr.Textbox(
                            label="Text to Add",
                            placeholder="Paste text content here...",
                            lines=5
                        )
                        add_text_btn = gr.Button("Add Text to Knowledge Base", variant="primary")
                        text_status = gr.Textbox(label="Text Addition Status", interactive=False)
                    
                    with gr.Column():
                        gr.Markdown("### Search Documents")
                        search_query = gr.Textbox(
                            label="Search Query",
                            placeholder="Enter search terms..."
                        )
                        search_btn = gr.Button("Search Documents", variant="primary")
                        search_results = gr.Textbox(
                            label="Search Results",
                            lines=10,
                            interactive=False
                        )
                        
                        gr.Markdown("### Knowledge Base Management")
                        clear_kb_btn = gr.Button("Clear Knowledge Base", variant="stop")
                        clear_kb_status = gr.Textbox(label="Clear Status", interactive=False)
            
            # Event handlers
            def handle_submit(message, history):
                if not message.strip():
                    return history, "", None, []
                
                res_history, res_msg, images = self.chat_response(message, history)
                
                # Obtener la última respuesta para convertirla a audio
                last_response = res_history[-1]["content"] if res_history else ""
                audio_path = self.voice_service.speak(last_response) if last_response else None
                
                return res_history, res_msg, audio_path, images

            submit_btn.click(
                handle_submit,
                inputs=[msg, chatbot],
                outputs=[chatbot, msg, audio_output, image_gallery]
            )
            
            msg.submit(
                handle_submit,
                inputs=[msg, chatbot],
                outputs=[chatbot, msg, audio_output, image_gallery]
            )
            
            clear_btn.click(
                self.clear_chat_history,
                outputs=[chatbot, clear_btn]
            )
            
            upload_btn.click(
                self.process_uploaded_files,
                inputs=[file_upload],
                outputs=[upload_status]
            )
            
            add_text_btn.click(
                self.add_text_to_knowledge_base,
                inputs=[text_input],
                outputs=[text_status]
            )
            
            search_btn.click(
                self.search_documents,
                inputs=[search_query],
                outputs=[search_results]
            )
            
            clear_kb_btn.click(
                self.clear_knowledge_base,
                outputs=[clear_kb_status]
            )
            
            refresh_status_btn.click(
                self.get_knowledge_base_status,
                outputs=[status_display]
            )
            
            # Update status after file upload
            upload_btn.click(
                self.get_knowledge_base_status,
                outputs=[status_display]
            )
            
            add_text_btn.click(
                self.get_knowledge_base_status,
                outputs=[status_display]
            )
            
            clear_kb_btn.click(
                self.get_knowledge_base_status,
                outputs=[status_display]
            )
        
        return interface
    
    def launch(self, **kwargs):
        """Launch the Gradio interface."""
        custom_css = """
        .chat-container {
            height: 500px;
        }
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        """
        interface = self.create_interface()
        return interface.launch(css=custom_css, **kwargs)
