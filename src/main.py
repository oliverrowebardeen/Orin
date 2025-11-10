import argparse
import os
import threading
import time
import sys
from datetime import datetime
from typing import List
from .reasoning import one_reasoning_run, self_consistency_reasoning

DEFAULT_MODEL = "deepseek-r1:8b"

# ANSI color codes
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

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
    Prints an ASCII art banner when Orin starts up.
    Uses simple ANSI escape codes for color (optional).
    """

    banner = f"""{CYAN}{BOLD}
   ___       _       
  / _ \\ _ __(_)_ __  
 | | | | '__| | '_ \\ 
 | |_| | |  | | | | |
  \\___/|_|  |_|_| |_|   {RESET}

{BOLD}Orin — local reasoning experiment (v0.1){RESET}
--------------------------------------------
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
                f.write(s.strip + "\n")
            f.write("\n=== Chosen answer ===\n")

        f.write(final_answer.strip() + "\n")

    print(f"[log] Saved session to {log_path}")

def main():
    """
    Defines CLi for Orin
    Handles:
    - parsing input
    - calling reasoning functions
    - printing + logging output
    """

    parser = argparse.ArgumentParser(
        description="Orin: compact local reasoning engine (v0.1 - CoT + self-consistency)"
    )
    parser.add_argument("question", nargs="*", help="Your question or prompt for Orin.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--temp", type=float, default=0.2, help="Temperature for single-run reasoning (default: 0.2)")
    parser.add_argument("--samples", type=int, default=1, help="If >1, use self-consistency with this many samples (default: 1)")

    args = parser.parse_args()

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
                model=args.model,
                n_samples=args.samples,
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
        print(f"\n[orin] Mode: single chain-of-thought run")

        # Start loading animation
        stop_event = threading.Event()
        loading_thread = threading.Thread(target=loading_animation, args=(stop_event,))
        loading_thread.start()
        
        try:
            answer = one_reasoning_run(
                question=question,
                model=args.model,
                temperature=args.temp,
            )
        finally:
            stop_event.set()
            loading_thread.join()

        print("\n=== Orin's answer ===\n")
        print(answer)
        print("\n=====================\n")

        log_session(question, answer, mode=mode, samples=None)

if __name__ == "__main__":
    print_orin_banner()
    main()
