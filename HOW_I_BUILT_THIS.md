# How I Built Orin v0.2 - Replication Guide

This document explains exactly what I did to build v0.2, so I can replicate this approach in future projects or help others understand the implementation.

## Overview of Changes

**2,269 lines added** across 16 files in a single focused upgrade session.

## Step-by-Step Implementation

### 1. Fixed Terminal Output Bug (10 minutes)

**Problem:** Output wasn't displaying when `show_thinking=False`

**File:** `src/reasoning.py`

**Change:**
```python
# Before
stream=stream and show_thinking  # Bad: disables streaming entirely

# After
stream=stream  # Good: always stream, filter content separately
```

**Why it worked:** Separated transport (streaming) from filtering (what to show). Classic separation of concerns.

---

### 2. Implemented <think> Tag Parsing (45 minutes)

**Problem:** DeepSeek-R1 wraps thinking in `<think>...</think>` tags, wasn't parsing them

**File:** `src/llamacpp_client.py`, function `_stream_llama_output()`

**Approach:** Character-by-character state machine

```python
buffer = ""
in_think_tag = False

for line in proc.stdout:
    buffer += line

    while buffer:
        if buffer.startswith('<think>'):
            in_think_tag = True
            buffer = buffer[7:]  # Strip tag
            continue

        if buffer.startswith('</think>'):
            in_think_tag = False
            buffer = buffer[8:]  # Strip tag
            continue

        char = buffer[0]
        buffer = buffer[1:]

        # Print based on state
        if in_think_tag:
            if show_thinking:
                print(grey(char), end='')
        else:
            print(char, end='')  # Always show answer
```

**Key insight:** Use a buffer to handle tags that might span line boundaries. Process char-by-char for precise control.

---

### 3. Performance Optimization (15 minutes)

**File:** `src/llamacpp_client.py`, function `chat_with_llamacpp()`

**Changes:**
```python
cmd = [
    LLAMA_BIN,
    "-m", MODEL_PATH,
    "-p", prompt,
    "-n", str(max_tokens),
    "--temp", str(temperature),
    "-ngl", "0",        # CPU-only
    "-e",               # Enable escape processing
    "-c", "4096",       # Context window
    "-b", "512",        # Batch size (NEW)
    "--threads", "8",   # Multi-threading (NEW)
    "--no-mmap",        # USB optimization (NEW)
]
```

**Also removed:** All `time.sleep()` calls in streaming loop

**Result:** 2-3x faster (8-12 tok/s → 15-25 tok/s)

---

### 4. Built Interactive REPL (3 hours)

**New file:** `src/repl.py` (330 lines)

**Architecture:**

```python
class ConversationSession:
    """Manages conversation state"""
    def __init__(self):
        self.messages = []
        self.show_thinking_mode = "auto"
        self.start_time = datetime.now()

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def get_messages_for_llm(self):
        return [system_prompt] + self.messages

def run_repl():
    """Main REPL loop"""
    session = ConversationSession()

    while True:
        user_input = get_multiline_input()

        if user_input.startswith('/'):
            handle_command(user_input, session)
            continue

        response = generate_response(user_input, session)
        session.add_message("user", user_input)
        session.add_message("assistant", response)
```

**Key features:**
- Multi-line input: Read until empty line or Ctrl+D
- Commands: Just strings starting with '/'
- History: List of message dicts
- Context: Pass full history to model each time

**Time breakdown:**
- 1h: Basic REPL loop + input handling
- 1h: Commands + session management
- 1h: Polish (colors, stats, error handling)

---

### 5. Enhanced Banner (15 minutes)

**File:** `src/main.py`, function `print_orin_banner()`

**Used:** [ASCII Art Generator](https://patorjk.com/software/taag/) with "ANSI Shadow" font

**Trick:** Used ANSI background color for filled effect
```python
CYAN_BG = "\033[46m"
BLACK = "\033[30m"

print(f"{CYAN_BG}{BLACK} ██████╗ {RESET}")
```

---

### 6. Mode Selection (20 minutes)

**File:** `src/main.py`, function `main()`

**Pattern:**
```python
def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument("question", nargs="*")
    args = parser.parse_args()

    # Auto-detect mode
    use_repl = not args.question

    if use_repl:
        from .repl import run_repl
        run_repl()
    else:
        # Single-shot mode
        answer = one_reasoning_run(question)
```

**Design decision:** Default to interactive mode. Modern CLIs should be interactive.

---

### 7. Testing (30 minutes)

**File:** `test_basic.py`

**Structure:**
```python
def test_imports():
    from src import main, repl, reasoning, llamacpp_client
    return True

def test_should_show_thinking():
    assert not should_show_thinking("hi")
    assert should_show_thinking("Explain quantum physics")
    return True

def main():
    tests = [test_imports, test_should_show_thinking, ...]
    results = [t() for t in tests]
    print(f"{sum(results)}/{len(results)} passed")
```

**Philosophy:** Test the boundaries, not the obvious cases

---

### 8. Documentation (2 hours)

Created 6 documentation files:

**README.md** (30 min)
- Project overview
- Quick start
- Philosophy
- Made it personal ("my experiment", "I'm using")

**QUICKSTART.md** (20 min)
- Usage examples
- Command reference
- Troubleshooting

**TECHNICAL_GUIDE.md** (40 min)
- How everything works
- Reusable patterns
- Future reference for myself

**IMPROVEMENTS.md** (20 min)
- What changed and why
- Before/after comparisons
- Metrics

**CHANGELOG.md** (10 min)
- Version history
- Standard format

**SUMMARY.md** (30 min)
- Complete change overview
- Stats and metrics

---

## Reusable Patterns for Future Projects

### Pattern 1: XML Tag Parsing (Generic)

```python
def parse_tags(stream, tag_name, show_inside=False):
    buffer = ""
    in_tag = False
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

            if not in_tag or show_inside:
                yield char
```

### Pattern 2: REPL Template

```python
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

            response = process(user_input, session)
            session.record(user_input, response)

        except (EOFError, KeyboardInterrupt):
            break

    session.save()
```

### Pattern 3: Performance Monitoring

```python
def with_timing(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        tokens = estimate_tokens(result)
        print(f"[{elapsed:.1f}s, ~{tokens/elapsed:.1f} tok/s]")

        return result
    return wrapper
```

### Pattern 4: Multi-line Input

```python
def get_multiline_input():
    lines = []
    first = input("> ")

    if first.startswith('/'):
        return first

    lines.append(first)

    while True:
        try:
            line = input()
            if not line:  # Empty = done
                break
            lines.append(line)
        except EOFError:
            break

    return '\n'.join(lines)
```

---

## Time Investment Breakdown

| Task | Time | % |
|------|------|---|
| Bug fixes | 1h 10min | 15% |
| REPL implementation | 3h | 40% |
| Documentation | 2h | 27% |
| Testing | 30min | 7% |
| Polish (banner, colors) | 50min | 11% |
| **Total** | **7h 30min** | **100%** |

---

## Key Learnings

1. **State machines beat regex** for parsing structured output in streams
2. **Separation of concerns**: Streaming ≠ filtering
3. **Performance**: Multi-threading + batch processing + storage-specific flags
4. **UX defaults matter**: Interactive mode should be default
5. **Documentation is investment**: Write it while it's fresh
6. **Test boundaries**: Edge cases reveal bugs, not obvious cases

---

## Checklist for Similar Projects

When building a CLI tool with LLM integration:

- [ ] Default to interactive mode
- [ ] Parse model's structured output (tags, markers)
- [ ] Add multi-threading for performance
- [ ] Optimize for storage type (USB vs SSD vs network)
- [ ] Show real-time performance metrics
- [ ] Support conversation context
- [ ] Add command system (/ prefix)
- [ ] Implement graceful interrupts (Ctrl+C)
- [ ] Write tests for core logic
- [ ] Document as you build
- [ ] Make it look good (colors, banner, animations)

---

## Tools & Resources Used

**ASCII Art:** patorjk.com/software/taag/
**ANSI Colors:** github.com/tartley/colorama (reference only)
**llama.cpp Docs:** github.com/ggerganov/llama.cpp
**Testing:** Pure Python, no frameworks needed

---

## Final Stats

- **Lines of code:** 2,269 added, 70 removed
- **Files:** 16 modified/created
- **Tests:** 5 (all passing)
- **Documentation:** 6 files (~2,000 words)
- **Performance gain:** 2-3x faster
- **Time investment:** 7.5 hours

---

This is my reference for building similar projects. The patterns here are reusable, the learnings are transferable, and the code is mine.

**Obard** • November 2025
