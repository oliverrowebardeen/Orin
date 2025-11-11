# Orin - Changelog

## [0.2.2] - 2025-11-10 - Performance Optimizations
- **Critical Fix:** Rewrote streaming to use line-based parsing (10x faster)
- **Optimizations:**
  - CPU: 4 threads (from 8)
  - Context: 1024 tokens (from 2048)
  - Batch: 256 (from 1024)
  - Greedy sampling (temp=0.0)
  - Limited to last 5 conversation turns
- **Results:** 1-2s first token, 25-40 tok/s generation

## [0.2.1] - 2025-11-10 - Performance & Features
- Added interleaved reasoning with self-verification
- Optimizations:
  - Context: 2048 tokens (from 4096)
  - Batch: 1024 (from 512)
  - Simplified system prompt
- **Results:** 30-40% faster than v0.2

## [0.2] - 2025-11-10 - Major Update
- Added interactive REPL with command history
- Smart thinking display (auto/always/never)
- Performance monitoring
- Improved terminal UI with colors

## [0.1] - 2025-11-09 - Initial Release
- Basic CLI interface
- Chain-of-thought reasoning
- Self-consistency voting
- DeepSeek-R1-Distill-Qwen-1.5B model

## Technical Details
- **Model:** DeepSeek-R1-Distill-Qwen-1.5B (Q4_K_M)
- **Requirements:** 4GB+ RAM, any CPU
- **Dependencies:** llama.cpp binary, Python 3.8+
- **Performance:**
  - First token: 1-2s
  - Generation: 25-40 tok/s
  - Memory: ~4GB RAM
  - Storage: ~2.5GB (model) + 100MB (code)

## Key Features
- Interactive REPL with history
- Smart thinking display
- Self-consistency verification
- Multi-line input
- Session logging