# Orin Reasoning Engine

A compact local reasoning engine that runs entirely from a USB drive, using Ollama as the backend with advanced reasoning orchestration.

## Features

- **Chain-of-Thought (CoT)**: Step-by-step reasoning with clear logical progression
- **Self-Consistency**: Multiple reasoning samples with voting for more reliable answers
- **Interleaved Reasoning**: Multi-agent dialogue between Analyst and Critic roles
- **RAG Support**: Placeholder for Retrieval-Augmented Generation (future implementation)
- **Offline Operation**: Runs entirely locally without internet dependencies
- **Comprehensive Logging**: All reasoning steps logged to console and timestamped files

## System Requirements

- Python 3.11+
- Ollama server running locally (`http://localhost:11434`)
- DeepSeek-R1-Distill-8B model pulled in Ollama
- ~2GB free space on USB drive

## Installation

1. Clone this repository to your USB drive:
```bash
git clone https://github.com/yourusername/Orin.git
cd Orin
```

2. Create virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Pull the DeepSeek model in Ollama:
```bash
ollama pull deepseek-r1-distill-8b:latest
```

## Usage

### Command Line Interface

**Single Query:**
```bash
python src/main.py query "Explain quantum computing in simple terms" --method cot
```

**Interactive Session:**
```bash
python src/main.py interactive
```

**Check System Status:**
```bash
python src/main.py status
```

### Reasoning Methods

- `cot`: Chain-of-Thought (default)
- `sc`: Self-Consistency with multiple samples
- `ir`: Interleaved Reasoning between agents

**Examples:**
```bash
# Chain of Thought reasoning
python src/main.py query "What are the ethical implications of AI?" --method cot

# Self-Consistency reasoning
python src/main.py query "Solve this math problem: 15 * 23 + 7" --method sc

# Interleaved Reasoning
python src/main.py query "Analyze the pros and cons of remote work" --method ir

# With RAG (when enabled)
python src/main.py query "How does photosynthesis work?" --method cot --rag
```

## Configuration

Edit `config.yaml` to customize:
- Model parameters (temperature, max tokens)
- Reasoning strategy settings
- RAG configuration
- Logging preferences

## Project Structure

```
Orin/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # CLI entry point and orchestrator
│   ├── reasoning.py         # Reasoning strategies and Ollama client
│   ├── rag.py               # RAG implementation (placeholder)
│   └── utils.py             # Logging, config, and utility functions
├── models/                  # Model storage (if needed)
├── rag_docs/               # Documents for RAG
├── rag_index/              # RAG vector index
├── logs/                   # Session logs
├── env/                    # Virtual environment
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Logging

All reasoning sessions are logged to:
- Console output (real-time)
- File: `logs/session_YYYYMMDD_HHMMSS.txt`

Logs include:
- Timestamps for all operations
- Intermediate reasoning steps
- Agent responses (for interleaved reasoning)
- System status and errors

## Development Roadmap

- [ ] Verifier loops and reflection mechanisms
- [ ] Tree-of-Thought branching exploration
- [ ] Lightweight RAG indexing with sentence transformers
- [ ] PDF document processing
- [ ] MCP (Model Context Protocol) integration
- [ ] Web interface for easier interaction
- [ ] Export reasoning traces to markdown

## Troubleshooting

**Ollama Connection Issues:**
1. Ensure Ollama is running: `ollama serve`
2. Check model is available: `ollama list`
3. Verify port 11434 is accessible

**Python Environment:**
1. Use Python 3.11 or higher
2. Activate virtual environment before running
3. Install all dependencies from requirements.txt

**Memory Issues:**
- Reduce `max_tokens` in config.yaml
- Lower `temperature` for more deterministic outputs
- Use CoT method instead of Self-Consistency for complex queries

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

**Orin** - Compact reasoning, powerful insights.
