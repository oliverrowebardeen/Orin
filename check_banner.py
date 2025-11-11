#!/usr/bin/env python3
import re

# Remove ANSI codes to count visible chars
def strip_ansi(text):
    return re.sub(r'\033\[[0-9;]*m', '', text)

banner_lines = [
    "╔══════════════════════════════════════════════════════════╗",
    "║   ██████╗ ██████╗ ██╗███╗   ██╗                         ║",
    "║  ██╔═══██╗██╔══██╗██║████╗  ██║                         ║",
    "║  ██║   ██║██████╔╝██║██╔██╗ ██║                         ║",
    "║  ██║   ██║██╔══██╗██║██║╚██╗██║                         ║",
    "║  ╚██████╔╝██║  ██║██║██║ ╚████║                         ║",
    "║   ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝                         ║",
    "║                                                          ║",
    "║  Local Reasoning Engine v0.2                             ║",
    "║  DeepSeek-R1-Distill-Qwen-1.5B • CPU-Optimized          ║",
    "║  Small models, big thinking                              ║",
    "╚══════════════════════════════════════════════════════════╝",
]

print("Checking banner alignment:")
print("=" * 60)
for i, line in enumerate(banner_lines, 1):
    visible = strip_ansi(line)
    length = len(visible)
    print(f"Line {i:2d}: {length} chars {'✓' if length == 60 else '✗ WRONG'}")
    if length != 60:
        print(f"         '{visible}'")
        print(f"         Missing: {60 - length} chars")
