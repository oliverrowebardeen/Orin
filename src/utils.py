"""
Utility functions for Orin reasoning engine.
Handles logging, configuration, and I/O operations.
"""

import yaml
import logging
import os
from datetime import datetime
from typing import Dict, Any
import sys


def load_config(config_path: str = "../config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}")
        sys.exit(1)


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """Setup logging configuration."""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO').upper())
    log_dir = log_config.get('log_dir', 'logs')
    console_output = log_config.get('console_output', True)
    file_output = log_config.get('file_output', True)
    
    # Create logs directory if it doesn't exist
    if file_output:
        os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('orin')
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if file_output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"session_{timestamp}.txt")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_reasoning_step(logger: logging.Logger, step_name: str, content: str):
    """Log a reasoning step with clear formatting."""
    logger.info(f"=== {step_name} ===")
    logger.info(content)
    logger.info("=" * (len(step_name) + 8))


def parse_ollama_response(response: str) -> str:
    """Parse and clean response from Ollama."""
    if not response:
        return ""
    
    # Remove any JSON artifacts if present
    lines = response.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('{') and not line.startswith('['):
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def validate_query(query: str) -> bool:
    """Validate user query."""
    if not query or not query.strip():
        return False
    return len(query.strip()) > 0


def format_agent_response(agent_name: str, response: str) -> str:
    """Format response from an reasoning agent."""
    return f"[{agent_name}]:\n{response}\n"
