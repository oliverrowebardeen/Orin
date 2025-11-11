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
        "-ngl", "0",  # CPU-only (explicitly disable GPU)
        "-c", "2048",  # Context window (enough for conversation history)
        "-t", "4",  # 4 threads (good for weak CPUs)
        "--no-mmap",  # Better for USB drives
        "-b", "256",  # Batch size (balanced for weak hardware)
        "--log-disable",  # Disable llama.cpp logs
        "--single-turn",  # Run for single turn, don't enter interactive mode
    ]

    if stream:
        return _stream_llama_output(cmd, show_thinking=show_thinking)
    else:
        return _get_llama_output(cmd)


def _stream_llama_output(cmd, show_thinking=True):
    """
    Stream output from llama-cli with robust filtering.
    ULTRA-SIMPLIFIED VERSION - wait for completion, then process.
    """
    import re

    GREY = '\033[90m'
    RESET = '\033[0m'

    # Run process and wait for completion (with timeout)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Combine stderr into stdout
        stdin=subprocess.PIPE,  # Provide a pipe (not DEVNULL)
        text=True,
    )

    try:
        # Close stdin immediately so llama knows there's no more input
        proc.stdin.close()

        # Wait for process to complete (with 60s timeout)
        stdout, _ = proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, _ = proc.communicate()
    except Exception as e:
        proc.kill()
        return f"Error: {e}"

    if not stdout:
        return "Error: No output from model"

    # Now process the complete output
    lines = stdout.split('\n')
    output_lines = []
    started = False
    in_think = False

    # Filter spam and extract generation
    for line in lines:
        # Skip debug output
        if any(x in line for x in ['warning:', 'llama_', 'print_info:', 'sampler',
                                     'generate: n_ctx', 'llama_perf', 'main:', 'build:',
                                     'Press Ctrl', 'EOF by user', 'memory breakdown',
                                     'interactive mode', 'system_info:', 'load:']):
            continue

        # Start capturing at "Assistant:"
        if 'Assistant:' in line:
            started = True
            line = line.split('Assistant:', 1)[-1]
            if not line.strip():
                continue

        if not started:
            continue

        # Handle thinking tags
        if '<think>' in line:
            in_think = True
            line = line.replace('<think>', '')
            if show_thinking:
                print(f"\n{GREY}", end='', flush=True)

        if '</think>' in line:
            if show_thinking:
                print(f"{RESET}", end='', flush=True)
            in_think = False
            line = line.replace('</think>', '')

        # Print and collect
        if line.strip():  # Skip empty lines
            output_lines.append(line)
            if not (in_think and not show_thinking):
                print(line, flush=True)

    result = '\n'.join(output_lines)

    # Clean up thinking tags if not showing
    if not show_thinking:
        result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)

    return result.strip()


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
