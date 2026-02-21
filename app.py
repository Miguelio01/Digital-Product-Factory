"""
Main application entry point for Digital-Product-Factory.
"""
import os
from dotenv import load_dotenv
from src.agent.rag_agent import RAGAgent
from src.interface.gradio_chat import ChatInterface

def main():
    # Load environment variables
    load_dotenv()
    
    print("🤖 Inicializando M.I.D.A.S. (Marketing Intelligence & Digital Automation System)...")
    print("🌐 Conectado a Qdrant Cloud - Nodo AWS sa-east-1")
    
    # Initialize the advanced agent
    agent = RAGAgent()
    
    # Initialize and launch the interface (using the correct class name: ChatInterface)
    interface = ChatInterface(agent, title="M.I.D.A.S. Digital Product Factory")
    interface.launch(share=True)

if __name__ == "__main__":
    main()
