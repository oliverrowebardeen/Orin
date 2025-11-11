# src/llamacpp_client.py

import subprocess
import os
from typing import List, Dict

# BASE_DIR = project root (folder that contains src/, bin/, models/)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Path to the llama.cpp binary on the USB
LLAMA_BIN = "/media/obard/69FE-3CAB/Orin/bin/llama/llama-cli"

# Path to the GGUF model on the USB
MODEL_PATH = "/media/obard/69FE-3CAB/Orin/models/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf"


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
    max_tokens: int = 4096,
    stream: bool = False,
    show_thinking: bool = True,
) -> str:
    """
    Call the llama.cpp binary with a prompt built from messages.
    Returns the generated text from stdout.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        temperature: Controls randomness (0.0 to 1.0)
        max_tokens: Maximum number of tokens to generate
        stream: Whether to stream the output
        show_thinking: Whether to show the model's thinking process
    If stream=True, prints output as it generates.
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
        "-ngl", "0",  # CPU-only
        "--ctx-size", "1024",  # Small context for speed on weak hardware
        "--threads", "4",  # Fewer threads (8 causes thrashing on weak CPUs)
        "--no-mmap",  # Better for USB drives
        "--log-disable",  # Disable logging
        "-b", "256",  # Small batch (less RAM, faster on weak hardware)
        "--n-predict", str(max_tokens),  # Explicit prediction limit
    ]

    if stream:
        return _stream_llama_output(cmd, show_thinking=show_thinking)
    else:
        return _get_llama_output(cmd)


def _stream_llama_output(cmd, show_thinking=True):
    """
    Stream output from llama-cli in real-time.
    Simplified for maximum speed - no fancy tag parsing.

    Args:
        cmd: Command to run
        show_thinking: Whether to show the model's thinking process
    """
    import sys
    import re

    # Define colors
    GREY = '\033[90m'
    RESET = '\033[0m'

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,  # Ignore stderr for speed
        stdin=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

    full_response = ""
    seen_assistant = False
    in_think_tag = False

    try:
        for line in iter(proc.stdout.readline, ''):
            # Skip loading/system info (minimal checks for speed)
            if 'llama_' in line or 'system_info:' in line or 'main:' in line:
                continue

            if not line.strip():
                continue

            # Wait for Assistant: marker
            if not seen_assistant:
                if "Assistant:" in line:
                    seen_assistant = True
                    line = line.split("Assistant:", 1)[-1]
                    if not line.strip():
                        continue
                else:
                    continue

            # Simple tag detection (line-based, not char-based)
            if '<think>' in line:
                in_think_tag = True
                line = line.replace('<think>', '')

            if '</think>' in line:
                in_think_tag = False
                line = line.replace('</think>', '')

            # Print and collect output
            if in_think_tag:
                if show_thinking:
                    print(f"{GREY}{line}{RESET}", end='', flush=True)
            else:
                # Always print non-thinking content
                print(line, end='', flush=True)
                full_response += line

    except KeyboardInterrupt:
        proc.terminate()
        if proc.poll() is None:
            proc.kill()
    finally:
        proc.wait()

    # Clean up any remaining tags
    full_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL)

    return full_response.strip()


def _get_llama_output(cmd):
    """
    Get complete output from llama-cli (non-streaming).
    Strips <think>...</think> tags to return only the final answer.
    """
    import signal
    import time
    import re

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        text=True,
    )

    try:
        stdout, stderr = proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        proc.terminate()
        time.sleep(2)
        if proc.poll() is None:
            proc.kill()
        stdout, stderr = proc.communicate()

    # Extract text after "Assistant:"
    if 'Assistant:' in stdout:
        stdout = stdout.split('Assistant:', 1)[-1]

    # Remove <think>...</think> tags and their content
    # Use DOTALL flag to match across newlines
    output = re.sub(r'<think>.*?</think>', '', stdout, flags=re.DOTALL)

    # Clean up extra whitespace
    output = '\n'.join(line for line in output.split('\n') if line.strip())

    return output.strip()
