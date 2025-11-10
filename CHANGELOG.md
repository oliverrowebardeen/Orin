# Changelog

All notable changes to Orin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2] - 2025-11-10

### Added
- **Interactive REPL mode** with Claude Code-style interface
- **Conversation history** and context awareness across turns
- **REPL commands**: `/help`, `/clear`, `/new`, `/thinking`, `/stats`, `/debug`, `/exit`
- **Smart thinking display** with three modes (auto/always/never)
- **Performance monitoring** with real-time token/sec metrics
- **Multi-line input support** (press Enter twice or Ctrl+D)
- **Session statistics** tracking (duration, message count, etc.)
- **Automatic session logging** to `logs/` directory
- **Blocky cyan-filled banner** for better branding
- **Color-coded output** (thinking in grey, answers in white)
- **Loading animations** with spinner during model loading
- **Comprehensive documentation** (README.md, QUICKSTART.md, IMPROVEMENTS.md)
- **Automated test suite** (test_basic.py)
- **Convenience launcher** (run.sh)

### Fixed
- **Terminal output not displaying** - Fixed streaming logic bug
- **should_show_thinking() not working** - Implemented proper `<think>` tag parsing
- **Extremely slow performance** - Removed artificial delays, added CPU optimization

### Changed
- **Performance improvements**: 2-3x faster generation with multi-threading
- **Better USB optimization**: Disabled memory mapping for better random access
- **Enhanced prompt building**: More structured system prompts
- **Improved error handling**: Graceful interrupts, timeouts, cleanup

### Performance
- First token latency: ~2-3s (was 3-5s)
- Generation speed: 15-25 tok/s (was 8-12 tok/s)
- CPU utilization: 8 threads (was 1 thread)
- Display lag: 0ms (was 10ms/char)

### Technical
- Added `src/repl.py` (11KB, 300+ lines)
- Modified `src/main.py` for mode selection
- Modified `src/reasoning.py` for better thinking logic
- Modified `src/llamacpp_client.py` for performance and tag parsing
- Fixed `src/__init__.py` naming (was `_init_.py`)

## [0.1] - 2025-11-09

### Added
- Initial release
- Basic CLI interface with single-shot questions
- Chain-of-thought reasoning
- Self-consistency voting (multiple samples)
- llama.cpp integration
- DeepSeek-R1-Distill-Qwen-1.5B model support
- Simple banner
- Basic logging

### Known Issues (Fixed in 0.2)
- Terminal output not displaying correctly
- Thinking always shows regardless of settings
- Very slow performance with artificial delays
- No conversation history
- No interactive mode
