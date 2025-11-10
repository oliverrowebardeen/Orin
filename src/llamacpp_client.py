# src/llamacpp_client.py

import subprocess
import os
from typing import List, Dict

# BASE_DIR = project root (folder that contains src/, bin/, models/)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Path to the llama.cpp binary on the USB
LLAMA_BIN = os.path.join(BASE_DIR, "bin", "llama")

# Path to the GGUF model on the USB
MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "DeepSeek-R1-Distill-Llama-8B-Q5_K_M.gguf",  # make sure this name matches exactly
)


def build_prompt_from_messages(messages: List[Dict[str, str]]) -> str:
    """
    Turn our list of role-based messages into a single prompt string
    that we pass to llama.cpp's -p flag.
    """
    parts: List[str] = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            parts.append(f"System: {content}\n")
        elif role == "user":
            parts.append(f"User: {content}\n")
        elif role == "assistant":
            parts.append(f"Assistant: {content}\n")
        else:
            parts.append(f"{role.capitalize()}: {content}\n")

    # End prompt where the assistant is supposed to continue.
    parts.append("Assistant:")

    return "\n".join(parts)


def chat_with_llamacpp(
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 512,
) -> str:
    """
    Call the llama.cpp binary with a prompt built from messages.
    Returns the generated text from stdout.
    """
    prompt = build_prompt_from_messages(messages)

    cmd = [
        LLAMA_BIN,
        "-m",
        MODEL_PATH,
        "-p",
        prompt,
        "-n",
        str(max_tokens),
        "--temp",
        str(temperature),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )

    return result.stdout.strip()
