# Orin v0.2 - Quick Start Guide

**Orin** is your personal local large-language-model lab running entirely offline from a USB drive. It uses the llama.cpp runtime with a small GGUF model (DeepSeek-R1-Distill-Qwen-1.5B) and explores how far a small model can be pushed through reasoning scaffolds.

## What's New in v0.2

✨ **Interactive REPL Mode** - Claude Code-style conversation interface
🎨 **Beautiful UI** - Blocky cyan banner, smooth animations, color-coded output
🧠 **Smart Thinking Display** - Automatically shows/hides reasoning based on query complexity
📊 **Performance Stats** - Real-time token/sec metrics and session statistics
💬 **Conversation History** - Context-aware multi-turn conversations
⚡ **CPU Optimized** - Blazing fast on Dell XPS with no GPU required

## Running Orin

### Interactive Mode (Default)
```bash
python -m src.main
```

This starts the REPL where you can have ongoing conversations with Orin.

### Single Question Mode
```bash
python -m src.main "What is the capital of France?"
```

### Self-Consistency Mode (Multiple Samples)
```bash
python -m src.main "Explain quantum entanglement" --samples 5
```

## REPL Commands

Once in interactive mode, you can use these commands:

| Command | Description |
|---------|-------------|
| `/help` | Show help message with all commands |
| `/clear` | Clear conversation history |
| `/new` | Start a new conversation session |
| `/thinking` | Toggle thinking display (auto/always/never) |
| `/stats` | Show session statistics |
| `/debug` | Show last raw model output for debugging |
| `/exit` | Exit Orin (or use Ctrl+C) |

## Input Tips

- **Type naturally** - just write your question and press Enter
- **Multi-line input** - press Enter on an empty line to submit (or Ctrl+D)
- **Interrupt generation** - press Ctrl+C to stop model generation
- **Auto thinking mode** - complex questions automatically show reasoning

## Examples

### Simple Question (No Thinking Display)
```
You: hi
[thinking: off]

Hello! I'm Orin, your local AI assistant. How can I help you today?
```

### Complex Question (With Thinking)
```
You: Explain how attention mechanisms work in transformers

[thinking: on]
[Thinking]
<model shows step-by-step reasoning in grey>

[Answer]
Attention mechanisms in transformers allow the model to...
```

### Multi-turn Conversation
```
You: What is Python?

Orin: Python is a high-level programming language...

You: Can you show me a hello world example?

Orin: Sure! Here's a simple Python hello world...
```

## Performance

**Hardware:** Dell XPS 11, 32GB RAM, USB 3.0, CPU-only
**Model:** DeepSeek-R1-Distill-Qwen-1.5B (Q4_K_M quantization)
**Expected Speed:** ~15-30 tokens/second (varies by complexity)

## Project Structure

```
Orin/
├── src/
│   ├── main.py              # Entry point & CLI
│   ├── repl.py              # Interactive REPL interface
│   ├── reasoning.py         # Reasoning strategies (CoT, self-consistency)
│   └── llamacpp_client.py   # llama.cpp integration
├── bin/
│   └── llama/               # llama.cpp binary
├── models/
│   └── *.gguf               # Model weights
└── logs/                    # Session logs
```

## Philosophy

Orin is an experiment in **small models, big thinking**. Rather than relying on massive parameter counts, we extract maximum reasoning, coherence, and reliability through:

- Chain-of-thought prompting
- Self-consistency voting
- Interleaved reasoning (coming soon)
- Structured thinking scaffolds

Everything is self-contained on the USB. No network, no external dependencies. Just pure local AI reasoning.

## Troubleshooting

**Model loads slowly?** - This is normal for USB drives. First load caches the model.

**Generation is slow?** - Check `/stats` to see token/sec. USB 3.0 speed and CPU capability affect performance.

**Thinking always shows?** - Use `/thinking` to toggle mode to `never` for cleaner output.

**Want to save a conversation?** - Logs are automatically saved to `logs/` directory on exit.

## Next Steps

- Try `/thinking` modes to see how reasoning display changes
- Experiment with complex analytical questions
- Use `/new` to start fresh conversations
- Check `logs/` to review past conversations
- Modify `src/reasoning.py` to add your own reasoning strategies

---

**Created by Obard** • Running on DeepSeek-R1-Distill-Qwen-1.5B • v0.2
