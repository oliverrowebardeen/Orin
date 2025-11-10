import argparse
import os
import threading
import time
import sys
from datetime import datetime
from typing import List
from .reasoning import one_reasoning_run, self_consistency_reasoning

# ANSI color codes
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"
GREY = "\033[90m"

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")

def loading_animation(stop_event):
    """
    Display a loading animation while the model is working.
    """
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f'\r{CYAN}{spinner[idx % len(spinner)]}{RESET}')
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * 30 + '\r')  # Clear the line
    sys.stdout.flush()

def print_orin_banner():
    """
    Prints a blocky ASCII art banner when Orin starts up.
    Filled with cyan color for maximum impact.
    """
    # Cyan background with black text for filled effect
    CYAN_BG = "\033[46m"
    BLACK = "\033[30m"

    banner = f"""
{CYAN}╔══════════════════════════════════════════════════════════╗
║  {CYAN_BG}{BLACK} ██████╗ ██████╗ ██╗███╗   ██╗ {RESET}{CYAN}                        ║
║  {CYAN_BG}{BLACK}██╔═══██╗██╔══██╗██║████╗  ██║ {RESET}{CYAN}                        ║
║  {CYAN_BG}{BLACK}██║   ██║██████╔╝██║██╔██╗ ██║ {RESET}{CYAN}                        ║
║  {CYAN_BG}{BLACK}██║   ██║██╔══██╗██║██║╚██╗██║ {RESET}{CYAN}                        ║
║  {CYAN_BG}{BLACK}╚██████╔╝██║  ██║██║██║ ╚████║ {RESET}{CYAN}                        ║
║  {CYAN_BG}{BLACK} ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ {RESET}{CYAN}                        ║
║                                                          ║
║  {BOLD}Local Reasoning Engine v0.2{RESET}{CYAN}                              ║
║  DeepSeek-R1-Distill-Qwen-1.5B • CPU-Optimized          ║
╚══════════════════════════════════════════════════════════╝{RESET}
"""
    print(banner)


def ensure_log_dir():
    """
    Ensure the log directory exists.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

def log_session(
    question: str,
    final_answer: str,
    mode: str,
    samples: List[str] | None = None,
):
    """
    Save everything from one run into a timestamped log file.
    Includes the question, the models answers, the final chosen answer.
    """

    ensure_log_dir()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(LOG_DIR, f"session_{ts}.txt")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("# Orin session\n")
        f.write(f"Timestamp : {ts}\n")
        f.write(f"Mode: {mode}\n\n")

        f.write("Question:\n")
        f.write(question.strip() + "\n\n")

        if samples is not None:
            f.write("=== All samples (self-consistency) ===\n")
            for i, s in enumerate(samples, start=1):
                f.write(f"\n--- Sample {i} ---\n")
                f.write(s.strip() + "\n")
            f.write("\n=== Chosen answer ===\n")

        f.write(final_answer.strip() + "\n")

    print(f"[log] Saved session to {log_path}")

def main():
    """
    Defines CLI for Orin
    Handles:
    - parsing input
    - calling reasoning functions
    - printing + logging output
    """

    parser = argparse.ArgumentParser(
        description="Orin: compact local reasoning engine (v0.2 - CoT + self-consistency + REPL)"
    )
    parser.add_argument("question", nargs="*", help="Your question or prompt for Orin. If omitted, starts interactive REPL mode.")
    parser.add_argument("--temp", type=float, default=0.2, help="Temperature for single-run reasoning (default: 0.2)")
    parser.add_argument("--samples", type=int, default=1, help="If >1, use self-consistency with this many samples (default: 1)")
    parser.add_argument("--repl", action="store_true", help="Start interactive REPL mode (default if no question provided)")
    parser.add_argument("--no-repl", action="store_true", help="Force single-shot mode even without question")

    args = parser.parse_args()

    # Determine if we should use REPL mode
    use_repl = args.repl or (not args.question and not args.no_repl)

    if use_repl:
        # Start interactive REPL
        from .repl import run_repl
        run_repl()
        return

    # Single-shot CLI mode
    question = " ".join(args.question) if args.question else input("Enter your question for Orin: ")

    if args.samples > 1:
        mode = f"self_consistency_{args.samples}"
        print(f"\n[orin] Mode: self-consistency with {args.samples} samples")
        # Start loading animation
        stop_event = threading.Event()
        loading_thread = threading.Thread(target=loading_animation, args=(stop_event,))
        loading_thread.start()
        
        try:
            best_answer, all_answers = self_consistency_reasoning(
                question=question,
                num_runs=args.samples,
                temperature=0.7
            )
        finally:
            stop_event.set()
            loading_thread.join()

        print(f"\n{CYAN}=== Orin's chosen answer (self-consistency) ==={RESET}\n")
        print(best_answer)
        print(f"\n{CYAN}=============================================={RESET}\n")
        log_session(question, best_answer, mode=mode, samples=all_answers)
    else:
        mode="single_run"
        print(f"\n[orin] Mode: single chain-of-thought run\n")
        
        # Start spinner during model loading
        stop_event = threading.Event()
        loading_thread = threading.Thread(target=loading_animation, args=(stop_event,))
        loading_thread.start()
        
        try:
            answer = one_reasoning_run(
                question=question,
                temperature=args.temp,
                stream=True,
            )
        finally:
            # Stop spinner when streaming starts
            stop_event.set()
            loading_thread.join()
            # Clear spinner line
            sys.stdout.write('\r' + ' ' * 30 + '\r')
            sys.stdout.flush()

        if not answer.strip():
            print(f"\n{CYAN}No final answer generated{RESET}\n")
        print(f"\n{CYAN}==================={RESET}\n")

        log_session(question, answer, mode=mode, samples=None)

if __name__ == "__main__":
    print_orin_banner()
    main()
