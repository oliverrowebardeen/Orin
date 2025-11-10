import argparse
import os
from datetime import datetime
from typing import List
from .reasoning import single_reasoning_run, self_consistency_reasoning

DEFAULT_MODEL = "deepseek-r1:8b"

LOG_DIR = os.path.join(os.path.dirname(_file_), "..", "logs")

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
    