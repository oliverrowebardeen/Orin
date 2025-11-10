import argparse
import os
from datetime import datetime
from typing import List
from .reasoning import single_reasoning_run, self_consistency_reasoning

DEFAULT_MODEL = "deepseek-r1:8b"

LOG_DIR = os.path.join(os.path.dirname(_file_), "..", "logs")

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