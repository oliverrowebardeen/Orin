# Orin - Local Reasoning Engine

```
╔══════════════════════════════════════════════════════════╗
║   ██████╗ ██████╗ ██╗███╗   ██╗                          ║
║  ██╔═══██╗██╔══██╗██║████╗  ██║                          ║
║  ██║   ██║██████╔╝██║██╔██╗ ██║                          ║
║  ██║   ██║██╔══██╗██║██║╚██╗██║                          ║
║  ╚██████╔╝██║  ██║██║██║ ╚████║                          ║
║   ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝                          ║
╚══════════════════════════════════════════════════════════╝
```

**A local AI reasoning lab that runs entirely offline from a USB drive**

---

## What is this?

Orin is my experiment in seeing how far you can push a tiny language model through clever prompt engineering and reasoning strategies. Instead of using massive 70B parameter models, I'm using a **1.5B parameter model** (DeepSeek-R1-Distill-Qwen) with reasoning scaffolds:

- Chain-of-thought prompting
- Self-consistency voting
- Transparent reasoning display
- Structured thinking frameworks

Everything runs 100% offline from my USB drive. No internet, no cloud APIs, no dependencies. Just local inference with llama.cpp.

---

## Features

### Interactive REPL
- Multi-line input (press Enter twice to submit)
- Real-time streaming responses
- Color-coded thinking vs final answers
- Conversation history & context
- Commands: `/help`, `/clear`, `/thinking`, `/stats`, etc.

### Smart Thinking Display
- **Auto mode**: Shows thinking for complex questions only
- **Always mode**: See full reasoning process
- **Never mode**: Clean answers only

### CPU-Optimized
- Multi-threaded generation
- USB-optimized (disabled mmap for better random access)
- No artificial delays
- 15-25 tokens/second on my Dell XPS 11

### Performance Monitoring
- Real-time token/sec display
- Session statistics
- Generation timing

---

## Quick Start

```bash
# Interactive mode (default)
./run.sh

# Single question
./run.sh "What is machine learning?"

# Self-consistency mode (multiple samples)
./run.sh "Explain quantum physics" --samples 5

# Help
./run.sh --help
```

---

## Project Structure

```
Orin/
├── src/
│   ├── main.py              # Entry point
│   ├── repl.py              # Interactive interface
│   ├── reasoning.py         # Reasoning strategies
│   └── llamacpp_client.py   # llama.cpp integration
├── bin/llama/               # llama.cpp binary
├── models/                  # GGUF model files
├── logs/                    # Session logs
└── tests/                   # Test suite
```

---

## Technical Details

**Model:** DeepSeek-R1-Distill-Qwen-1.5B (Q4_K_M quantization, ~1GB)
**Hardware:** Dell XPS 11, 32GB RAM, USB 3.0, CPU-only
**Performance:** 15-25 tok/s, 2-3s first token latency
**Dependencies:** Python 3.8+, llama.cpp (no pip packages needed)

### Why these choices?

**Small model**: Fits on USB, fast enough for interactive use, transparent reasoning
**CPU-only**: No GPU needed, works anywhere
**USB drive**: Completely portable, no installation required
**No dependencies**: Pure Python stdlib + llama.cpp binary

---

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Getting started guide
- **[COMPLETE_CHANGELOG.md](COMPLETE_CHANGELOG.md)** - Version history

---

## Philosophy

The core idea: **intelligence isn't just about size**. By adding reasoning scaffolds, we can make a 1.5B model more reliable and transparent than a 70B model running in a black box.

### Chain-of-Thought (CoT)
Model shows its reasoning steps before answering. Improves accuracy on complex tasks.

### Self-Consistency
Generate multiple answers with higher temperature, vote for most common. Reduces errors and hallucinations.

### Interleaved Reasoning (planned)
Alternate between thinking and verification. Self-correct mid-generation.

---

## Testing

```bash
python3 test_basic.py
```

All 5 tests should pass:
- Module imports
- Banner display
- Thinking logic
- Message builder
- Conversation session

---

## Roadmap

### v0.3
- Interleaved reasoning
- Syntax highlighting
- Export conversations
- Prompt templates
- Multi-model support

### Future
- RAG integration
- Speed improvements
- Tool use
- Fine-tuning pipeline

---

## License

MIT - do whatever you want with this.

---

## Acknowledgments

- llama.cpp team for the inference engine
- DeepSeek for the distilled reasoning model

---

**Built by Obard** • Version 0.2 • November 2025

*Small model, big thinking*
