import requests
from typing import List, Dict, Optional


OLLAMA_URL = "http://localhost:11434/api/chat"  # default Ollama chat endpoint


def chat_with_ollama(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    stream: bool = False,
) -> str:
    """
    Simple wrapper around Ollama's /api/chat endpoint.
    messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
    Returns the full assistant response as a string.
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": temperature,
        },
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
    resp.raise_for_status()

    # If we requested non-streaming, Ollama returns a JSON with 'message'
    data = resp.json()
    return data["message"]["content"]
