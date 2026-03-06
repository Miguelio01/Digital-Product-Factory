import subprocess
import os
from langchain_core.tools import tool

@tool
def bash_executor(command: str) -> str:
    """Ejecuta comandos de terminal locales."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return f'STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}'
    except Exception as e: return f'Error: {str(e)}'

@tool
def file_manager(action: str, path: str, content: str = "") -> str:
    """Gestiona archivos (read, write, mkdir)."""
    try:
        abs_path = os.path.abspath(path)
        if action == 'write':
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, 'w') as f: f.write(content)
            return f'Guardado: {path}'
        if action == 'read':
            with open(abs_path, 'r') as f: return f.read()
        return 'Acción no válida.'
    except Exception as e: return f'Error: {str(e)}'

SYSTEM_TOOLS = [bash_executor, file_manager]
