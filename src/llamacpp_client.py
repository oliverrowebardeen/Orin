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
        "-ngl", "0",  # CPU-only (no GPU on Dell XPS)
        "-e",
        "-c", "4096",  # Context window
        "-b", "512",  # Batch size for prompt processing
        "--threads", "8",  # Use multiple CPU threads
        "--no-mmap",  # Disable memory mapping for USB (faster random access)
    ]

    if stream:
        return _stream_llama_output(cmd, show_thinking=show_thinking)
    else:
        return _get_llama_output(cmd)


def _stream_llama_output(cmd, show_thinking=True):
    """
    Stream output from llama-cli in real-time.
    Parses <think>...</think> tags from DeepSeek-R1 model output.

    Args:
        cmd: Command to run
        show_thinking: Whether to show the model's thinking process
    """
    import sys
    import time

    # Define colors
    GREY = '\033[90m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

    full_response = ""
    full_output = ""  # Capture everything for logging
    seen_assistant = False
    in_think_tag = False
    buffer = ""

    try:
        for line in iter(proc.stdout.readline, ''):
            # Skip loading/system info
            if any(skip in line for skip in ['llama_model_loader:', 'print_info:', 'load_tensors:',
                                             'llama_context:', 'llama_kv_cache:', 'system_info:',
                                             'main:', 'sampler', 'generate:', '== Running']):
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

            # Add to buffer for tag parsing
            buffer += line
            full_output += line

            # Process buffer character by character to handle tags
            while buffer:
                # Check for <think> tag
                if buffer.startswith('<think>'):
                    in_think_tag = True
                    buffer = buffer[7:]  # Remove '<think>'
                    if show_thinking:
                        print(f"\n{GREY}[Thinking]{RESET}\n", flush=True)
                    continue

                # Check for </think> tag
                if buffer.startswith('</think>'):
                    in_think_tag = False
                    buffer = buffer[8:]  # Remove '</think>'
                    if show_thinking:
                        print(f"\n{CYAN}[Answer]{RESET}\n", flush=True)
                    continue

                # Print character if appropriate
                char = buffer[0]
                buffer = buffer[1:]

                if in_think_tag:
                    # Inside thinking - only show if requested
                    if show_thinking:
                        print(f"{GREY}{char}{RESET}", end='', flush=True)
                else:
                    # Outside thinking - always show (this is the answer)
                    print(char, end='', flush=True)
                    full_response += char

    except KeyboardInterrupt:
        proc.terminate()
        time.sleep(1)
        if proc.poll() is None:
            proc.kill()
    finally:
        proc.wait()

    # Return just the answer (outside think tags) or full output if no tags found
    return full_response.strip() if full_response.strip() else full_output.strip()


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
