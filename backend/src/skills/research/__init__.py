from langchain_core.tools import tool
from duckduckgo_search import DDGS

@tool
def web_search(query: str) -> str:
    """Realiza una búsqueda profunda en internet."""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
            return '\n\n'.join([f'Title: {r["title"]}\nLink: {r["href"]}' for r in results])
    except Exception as e: return f'Error: {str(e)}'

RESEARCH_TOOLS = [web_search]
