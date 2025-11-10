# src/llamacpp_client.py

import subprocess
import os
from typing import List, Dict

# BASE_DIR = project root (folder that contains src/, bin/, models/)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Path to the llama.cpp binary on the USB
LLAMA_BIN = "/home/obard/llama.cpp/main"

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
) -> str:
    """
    Call the llama.cpp binary with a prompt built from messages.
    Returns the generated text from stdout.
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
        "-ngl", "0",
        "-e",
    ]

    if stream:
        return _stream_llama_output(cmd)
    else:
        return _get_llama_output(cmd)


def _stream_llama_output(cmd):
    """
    Stream output from llama-cli in real-time.
    """
    import sys
    import time
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    
    full_response = ""
    seen_assistant = False
    
    try:
        for line in iter(proc.stdout.readline, ''):
            # Skip loading/system info
            if any(skip in line for skip in ['llama_model_loader:', 'print_info:', 'load_tensors:', 'llama_context:', 'llama_kv_cache:', 'system_info:', 'main:', 'sampler', 'generate:', '== Running']):
                continue
            
            # Check if we're transitioning from thinking to final answer
            if not capturing_answer and any(phrase in line for phrase in ["In summary,", "In essence,", "In conclusion,", "Here's a structured summary", "Putting it all together"]):
                capturing_answer = True
                in_thinking = False
                if show_thinking:
                    print(f"\n{CYAN}=== Final Answer ==={RESET}\n")
            
            # Determine if this is thinking content
            is_thinking = not capturing_answer
            
            # Stream with typing effect
            if show_thinking or not is_thinking:
                for char in line:
                    if not is_thinking or not show_thinking:
                        # Final answer in normal color
                        print(char, end='', flush=True)
                    elif show_thinking and is_thinking:
                        # Thinking in grey
                        print(f"{GREY}{char}{RESET}", end='', flush=True)
                    time.sleep(0.01)
            
            # Only add to response if we're capturing the final answer
            if capturing_answer:
                full_response += line
                
    except KeyboardInterrupt:
        proc.terminate()
        time.sleep(1)
        if proc.poll() is None:
            proc.kill()
    finally:
        proc.wait()
    
    return full_response.strip()


def _get_llama_output(cmd):
    """
    Get complete output from llama-cli (non-streaming).
    """
    import signal
    import time
    
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
    
    # Extract only the actual response
    lines = stdout.split('\n')
    response_lines = []
    
    for i, line in enumerate(lines):
        if 'Assistant:' in line:
            # Get everything after the last "Assistant:"
            response_lines = [l for l in lines[i+1:] if l.strip()]
            break
    
    return '\n'.join(response_lines).strip() if response_lines else stdout.strip()
