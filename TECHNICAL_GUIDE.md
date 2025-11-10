# Technical Guide - How I Built Orin v0.2

This document explains exactly what I changed and why, so I can replicate this approach in future projects.

## Problem 1: Terminal Output Not Displaying

### The Bug
In `src/reasoning.py`, line 101 had this logic:
```python
stream=stream and show_thinking  # Only stream if thinking should be shown
```

This meant when `show_thinking=False`, streaming was disabled entirely, so nothing appeared in the terminal.

### The Fix
Changed to:
```python
stream=stream  # Always stream to show output in real-time
```

Now `show_thinking` only controls what content is displayed, not whether to stream.

**Key Learning:** Separate concerns - streaming (transport) vs filtering (content).

---

## Problem 2: should_show_thinking() Not Working

### The Bug
The DeepSeek-R1 model outputs thinking wrapped in `<think>...</think>` XML tags. My code wasn't parsing these, so thinking always displayed regardless of the `show_thinking` setting.

### The Fix
Completely rewrote `_stream_llama_output()` in `src/llamacpp_client.py`:

```python
def _stream_llama_output(cmd, show_thinking=True):
    buffer = ""
    in_think_tag = False

    for line in iter(proc.stdout.readline, ''):
        buffer += line

        while buffer:
            # Check for <think> opening tag
            if buffer.startswith('<think>'):
                in_think_tag = True
                buffer = buffer[7:]  # Remove the tag
                continue

            # Check for </think> closing tag
            if buffer.startswith('</think>'):
                in_think_tag = False
                buffer = buffer[8:]  # Remove the tag
                continue

            # Print character based on context
            char = buffer[0]
            buffer = buffer[1:]

            if in_think_tag:
                if show_thinking:
                    print(f"{GREY}{char}{RESET}", end='')
            else:
                print(char, end='')  # Always show final answer
```

**Key Learning:** When a model uses structured output (XML tags), parse it character-by-character using a state machine.

### State Machine Logic
- `in_think_tag = False` → Normal output (answer)
- `in_think_tag = True` → Thinking output (optional display)

---

## Problem 3: Slow Performance

### The Problems
1. Artificial delays: `time.sleep(0.01)` on every character
2. Single-threaded execution
3. Memory mapping issues with USB drives
4. No batch processing

### The Fixes

#### 1. Remove Artificial Delays
Deleted all `time.sleep()` calls in the streaming loop. They were adding ~10ms per character for a "typing effect" but this made it unbearably slow.

#### 2. Add Multi-Threading
Added `--threads 8` to llama.cpp command:
```python
"--threads", "8",  # Use multiple CPU threads
```

This parallelizes token generation across CPU cores.

#### 3. Optimize for USB
Added `--no-mmap` flag:
```python
"--no-mmap",  # Disable memory mapping for USB
```

Memory mapping (mmap) is great for SSDs but terrible for USB drives because it assumes fast random access. Disabling it forces sequential reads which USB handles better.

#### 4. Add Batch Processing
Added batch size flag:
```python
"-b", "512",  # Batch size for prompt processing
```

This processes the input prompt in larger chunks rather than token-by-token.

**Result:** ~2-3x faster (15-25 tok/s vs 8-12 tok/s)

---

## Feature: Interactive REPL

### Design Pattern: Session-Based State Management

Created `src/repl.py` with a `ConversationSession` class:

```python
class ConversationSession:
    def __init__(self):
        self.messages = []  # Conversation history
        self.show_thinking_mode = "auto"
        self.start_time = datetime.now()

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def get_messages_for_llm(self):
        # Returns system prompt + all history
        return [{"role": "system", "content": self.system_prompt}] + self.messages
```

### Multi-Line Input Pattern

```python
def get_multiline_input(prompt_text="You"):
    lines = []
    first_line = input()

    if first_line.startswith('/'):  # Command
        return first_line

    lines.append(first_line)

    while True:
        line = input()
        if not line:  # Empty line = submit
            break
        lines.append(line)

    return '\n'.join(lines).strip()
```

**Key Learning:** Use empty line as submission signal. Feels natural for users.

### Command System Pattern

```python
while True:
    user_input = get_multiline_input()

    if user_input.startswith('/'):
        cmd = user_input.lower().strip()

        if cmd == '/exit':
            break
        elif cmd == '/clear':
            session.clear_history()
        # ... more commands
        continue

    # Normal message processing
    process_message(user_input)
```

**Key Learning:** Commands are just strings with special handling. Keep it simple.

---

## Feature: Performance Monitoring

### Token Counting Heuristic

```python
tokens_estimate = len(response.split()) * 1.3
tokens_per_sec = tokens_estimate / elapsed
```

Rough estimate: words × 1.3 ≈ tokens (works reasonably well for English)

### Display Pattern

```python
start_time = time.time()
# ... generate response ...
elapsed = time.time() - start_time

print(f"\n[{elapsed:.1f}s, ~{tokens_per_sec:.1f} tok/s]\n")
```

**Key Learning:** Users love seeing performance metrics. It makes the system feel transparent.

---

## Feature: Smart Thinking Detection

### Pattern Matching Approach

```python
def should_show_thinking(question: str) -> bool:
    question_lower = question.lower().strip()

    # Simple patterns (no thinking needed)
    simple_patterns = [
        r'^(hi|hello|hey)$',
        r'^(thanks|bye)$',
    ]

    # Complex patterns (thinking helpful)
    complex_patterns = [
        r'what is',
        r'explain',
        r'how does',
        r'analyze',
    ]

    # Check patterns
    for pattern in simple_patterns:
        if re.match(pattern, question_lower):
            return False

    for pattern in complex_patterns:
        if re.search(pattern, question_lower):
            return True

    # Fallback: long questions need thinking
    return len(question.split()) > 10
```

**Key Learning:** Heuristics beat ML for simple classification. Regex + word count is fast and transparent.

---

## Architecture Pattern: Mode Selection

### Entry Point Design

```python
def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument("question", nargs="*")
    parser.add_argument("--repl", action="store_true")

    args = parser.parse_args()

    # Determine mode
    use_repl = args.repl or (not args.question and not args.no_repl)

    if use_repl:
        from .repl import run_repl
        run_repl()
        return

    # Single-shot mode
    question = " ".join(args.question)
    answer = one_reasoning_run(question)
    print(answer)
```

**Key Learning:** Default to interactive mode if no args provided. Users expect modern CLIs to be interactive.

---

## Testing Strategy

### Unit Test Pattern

```python
def test_should_show_thinking():
    # Simple cases
    assert not should_show_thinking("hi")
    assert not should_show_thinking("thanks")

    # Complex cases
    assert should_show_thinking("What is machine learning?")
    assert should_show_thinking("Explain transformers")

    # Edge case: long question
    long_question = " ".join(["word"] * 15)
    assert should_show_thinking(long_question)
```

**Key Learning:** Test edge cases and the boundaries between categories.

---

## Performance Optimization Checklist

For any llama.cpp deployment:

1. **Threading**: `--threads N` where N = CPU cores
2. **Batch size**: `-b 512` or higher for faster prompt processing
3. **Context**: `-c 4096` (or model's max) to allow longer conversations
4. **Memory**: `--no-mmap` for USB/network drives
5. **GPU layers**: `-ngl 0` for CPU-only, `-ngl 999` for max GPU
6. **Quantization**: Q4_K_M is sweet spot (size vs quality)

---

## Replication Guide for Future Environments

### 1. Basic Setup

```bash
# Structure
project/
├── src/
│   ├── __init__.py
│   ├── main.py        # Entry point
│   ├── repl.py        # Interactive mode
│   ├── client.py      # LLM integration
│   └── logic.py       # Core logic
├── bin/               # Binaries
├── models/            # Model files
├── logs/              # Session logs
└── tests/             # Test files

# Essential files
touch src/__init__.py
touch README.md
touch .gitignore
touch VERSION
```

### 2. llama.cpp Integration Pattern

```python
# client.py
def chat(messages, temperature=0.2, stream=False):
    cmd = [
        "/path/to/llama-cli",
        "-m", "/path/to/model.gguf",
        "-p", build_prompt(messages),
        "-n", "2048",
        "--temp", str(temperature),
        "--threads", "8",
        "-b", "512",
        "--no-mmap",  # If on USB/network
    ]

    if stream:
        return stream_output(cmd)
    else:
        return get_output(cmd)
```

### 3. Tag Parsing Pattern (Reusable)

```python
def parse_xml_stream(stream, tag_name, show_tagged_content=False):
    """
    Generic XML tag parser for streaming output.

    Args:
        stream: Iterator yielding lines
        tag_name: Tag to detect (e.g., "think")
        show_tagged_content: Whether to display content inside tags
    """
    buffer = ""
    in_tag = False
    content_inside = ""
    content_outside = ""

    open_tag = f"<{tag_name}>"
    close_tag = f"</{tag_name}>"

    for line in stream:
        buffer += line

        while buffer:
            if buffer.startswith(open_tag):
                in_tag = True
                buffer = buffer[len(open_tag):]
                continue

            if buffer.startswith(close_tag):
                in_tag = False
                buffer = buffer[len(close_tag):]
                continue

            char = buffer[0]
            buffer = buffer[1:]

            if in_tag:
                content_inside += char
                if show_tagged_content:
                    print(char, end='')
            else:
                content_outside += char
                print(char, end='')

    return content_outside, content_inside
```

### 4. REPL Template (Reusable)

```python
# repl.py template
def run_repl():
    session = Session()

    while True:
        try:
            user_input = get_input()

            if not user_input:
                continue

            if user_input.startswith('/'):
                if not handle_command(user_input, session):
                    break  # /exit
                continue

            # Process normal input
            response = generate_response(user_input, session)
            session.add_exchange(user_input, response)

        except (EOFError, KeyboardInterrupt):
            break

    save_session(session)
```

### 5. Performance Monitoring Template

```python
import time

def timed_generation(generate_func, *args, **kwargs):
    start = time.time()
    result = generate_func(*args, **kwargs)
    elapsed = time.time() - start

    # Estimate tokens (rough heuristic)
    tokens = len(result.split()) * 1.3
    tok_per_sec = tokens / elapsed if elapsed > 0 else 0

    print(f"\n[{elapsed:.1f}s, ~{tok_per_sec:.1f} tok/s]\n")
    return result
```

### 6. Testing Template

```python
# test_basic.py
def test_imports():
    try:
        from src import main, repl, client, logic
        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False

def test_core_logic():
    from src.logic import some_function

    assert some_function("input") == "expected"
    assert some_function("edge_case") == "expected_edge"

    return True

if __name__ == "__main__":
    tests = [test_imports, test_core_logic, ...]
    results = [t() for t in tests]
    print(f"{sum(results)}/{len(results)} passed")
```

---

## Color Coding Reference

```python
# ANSI escape codes
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'

# Colors
BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'

# Bright colors
GREY = '\033[90m'
BRIGHT_CYAN = '\033[96m'

# Background
BG_CYAN = '\033[46m'

# Usage
print(f"{CYAN}Colored text{RESET}")
print(f"{BG_CYAN}{BLACK}Filled banner{RESET}")
```

---

## Key Takeaways

1. **Streaming + Parsing**: Use character-by-character state machines for structured output
2. **Performance**: Multi-threading + batch processing + storage-specific flags
3. **UX**: Interactive mode should be default, commands are just strings
4. **Testing**: Unit tests for pure functions, integration tests for full flow
5. **Documentation**: Write it for your future self who forgot everything

---

This is my reference for building similar projects in the future.
