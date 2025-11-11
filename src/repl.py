"""
Interactive REPL interface for Orin.
Claude Code-style conversation interface with history and commands.
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import List, Dict, Optional
from .reasoning import one_reasoning_run, should_show_thinking
from .llamacpp_client import chat_with_llamacpp

# ANSI color codes
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"
GREY = "\033[90m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
DIM = "\033[2m"

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")


class ConversationSession:
    """Manages a conversation session with history and context."""

    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.show_thinking_mode = "auto"  # auto, always, never
        self.reasoning_mode = "standard"  # standard, interleaved
        self.start_time = datetime.now()
        self.total_tokens = 0
        self.total_questions = 0

        # Shorter system prompt for faster processing
        self.system_prompt = (
            "You are Orin, a helpful AI assistant. Be concise, clear, and accurate. "
            "Think step-by-step for complex questions."
        )

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append({"role": role, "content": content})

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Get formatted messages including system prompt."""
        return [{"role": "system", "content": self.system_prompt}] + self.messages

    def clear_history(self):
        """Clear conversation history but keep system prompt."""
        self.messages = []
        self.total_questions = 0
        print(f"{GREEN}✓ Conversation history cleared{RESET}")

    def get_stats(self) -> str:
        """Get session statistics."""
        duration = datetime.now() - self.start_time
        mins = int(duration.total_seconds() / 60)
        secs = int(duration.total_seconds() % 60)

        return f"{GREY}Session: {mins}m {secs}s | Messages: {len(self.messages)} | Questions: {self.total_questions}{RESET}"


def print_help():
    """Display help information for REPL commands."""
    help_text = f"""
{CYAN}{BOLD}Orin REPL Commands:{RESET}

{GREEN}/help{RESET}         Show this help message
{GREEN}/clear{RESET}        Clear conversation history
{GREEN}/new{RESET}          Start a new conversation session
{GREEN}/thinking{RESET}     Toggle thinking display mode (auto/always/never)
{GREEN}/interleaved{RESET}  Toggle interleaved reasoning (model verifies answers)
{GREEN}/stats{RESET}        Show session statistics
{GREEN}/debug{RESET}        Show last raw model output for debugging
{GREEN}/exit{RESET}         Exit Orin (or use Ctrl+C)

{CYAN}{BOLD}Tips:{RESET}
• Type naturally - no special syntax needed
• Press Enter twice to submit (or Ctrl+D)
• Use Ctrl+C to interrupt generation
• Thinking mode 'auto' shows reasoning for complex questions only

{CYAN}{BOLD}Examples:{RESET}
  What is the capital of France?
  Explain how transformers work in machine learning
  Write a Python function to calculate fibonacci numbers
"""
    print(help_text)


def loading_animation(stop_event, message="Thinking"):
    """Display a loading animation while the model is working."""
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f'\r{CYAN}{spinner[idx % len(spinner)]} {message}...{RESET}')
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * 50 + '\r')  # Clear the line
    sys.stdout.flush()


def get_multiline_input(prompt_text: str = "You") -> Optional[str]:
    """
    Get multiline input from user.
    Returns None if user wants to exit.
    """
    lines = []
    print(f"\n{CYAN}{BOLD}{prompt_text}:{RESET}", end=" ")

    try:
        # Read first line
        first_line = input()

        # Check for commands
        if first_line.startswith('/'):
            return first_line

        lines.append(first_line)

        # If first line is not empty, allow multiline
        # User can press Enter on empty line to finish, or Ctrl+D
        while True:
            try:
                line = input()
                if not line:  # Empty line = done
                    break
                lines.append(line)
            except EOFError:  # Ctrl+D
                break

        return '\n'.join(lines).strip()

    except (EOFError, KeyboardInterrupt):
        print()  # New line
        return None


def run_repl():
    """Main REPL loop for Orin."""
    session = ConversationSession()
    last_raw_output = ""

    print(f"\n{GREY}Type your message and press Enter. Use /help for commands.{RESET}")
    print(f"{GREY}Press Enter twice or Ctrl+D to submit. Ctrl+C to interrupt.{RESET}\n")

    while True:
        # Show session stats occasionally
        if session.total_questions > 0 and session.total_questions % 5 == 0:
            print(f"\n{session.get_stats()}\n")

        # Get user input
        user_input = get_multiline_input()

        if user_input is None:  # EOF or interrupt
            print(f"\n{CYAN}Goodbye!{RESET}")
            break

        if not user_input.strip():
            continue

        # Handle commands
        if user_input.startswith('/'):
            cmd = user_input.lower().strip()

            if cmd == '/exit' or cmd == '/quit':
                print(f"\n{CYAN}Goodbye!{RESET}")
                break

            elif cmd == '/help':
                print_help()
                continue

            elif cmd == '/clear':
                session.clear_history()
                continue

            elif cmd == '/new':
                # Save old session
                if session.messages:
                    save_session_log(session)
                session = ConversationSession()
                print(f"{GREEN}✓ Started new conversation session{RESET}")
                continue

            elif cmd == '/thinking':
                modes = ['auto', 'always', 'never']
                current_idx = modes.index(session.show_thinking_mode)
                next_mode = modes[(current_idx + 1) % len(modes)]
                session.show_thinking_mode = next_mode
                print(f"{GREEN}✓ Thinking display mode: {BOLD}{next_mode}{RESET}")
                continue

            elif cmd == '/interleaved':
                if session.reasoning_mode == "standard":
                    session.reasoning_mode = "interleaved"
                    print(f"{GREEN}✓ Interleaved reasoning: {BOLD}ON{RESET} (model verifies its own answers)")
                else:
                    session.reasoning_mode = "standard"
                    print(f"{GREEN}✓ Interleaved reasoning: {BOLD}OFF{RESET}")
                continue

            elif cmd == '/stats':
                print(f"\n{session.get_stats()}")
                print(f"{GREY}System: {session.system_prompt[:100]}...{RESET}\n")
                continue

            elif cmd == '/debug':
                if last_raw_output:
                    print(f"\n{GREY}=== Last Raw Output ==={RESET}")
                    print(last_raw_output)
                    print(f"{GREY}=== End Raw Output ==={RESET}\n")
                else:
                    print(f"{YELLOW}No output to show yet{RESET}")
                continue

            else:
                print(f"{YELLOW}Unknown command: {cmd}. Type /help for available commands.{RESET}")
                continue

        # Add user message to history
        session.add_message("user", user_input)
        session.total_questions += 1

        # Determine if we should show thinking
        if session.show_thinking_mode == "always":
            show_thinking = True
        elif session.show_thinking_mode == "never":
            show_thinking = False
        else:  # auto
            show_thinking = should_show_thinking(user_input)

        # Show what mode we're in for this query
        thinking_indicator = f"{GREY}[thinking: {'on' if show_thinking else 'off'}]{RESET} "
        print(f"\n{thinking_indicator}", end='')

        # Start thinking animation
        stop_event = threading.Event()
        loading_thread = threading.Thread(
            target=loading_animation,
            args=(stop_event, "Thinking")
        )
        loading_thread.start()

        # Get response
        try:
            start_time = time.time()

            # Choose reasoning strategy
            if session.reasoning_mode == "interleaved":
                # Use interleaved reasoning (slower but more accurate)
                from .reasoning import interleaved_reasoning
                from .llamacpp_client import chat_with_llamacpp

                # Build messages
                messages = session.get_messages_for_llm()

                # Initial response
                print(f"\n{GREY}[Step 1: Initial answer]{RESET}\n")
                response = chat_with_llamacpp(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=512,
                    stream=True,
                    show_thinking=show_thinking,
                )

                # Verification step
                print(f"\n{GREY}[Step 2: Verification]{RESET}\n")
                verify_msg = messages + [
                    {"role": "assistant", "content": response},
                    {"role": "user", "content": "Verify your answer. Any corrections needed?"}
                ]
                verification = chat_with_llamacpp(
                    messages=verify_msg,
                    temperature=0.2,
                    max_tokens=256,
                    stream=True,
                    show_thinking=False,
                )

                # If verification suggests changes, use those
                if not any(word in verification.lower() for word in ["correct", "verified", "good", "accurate"]):
                    response = verification

            else:
                # Standard mode
                from .llamacpp_client import chat_with_llamacpp
                response = chat_with_llamacpp(
                    messages=session.get_messages_for_llm(),
                    temperature=0.2,
                    max_tokens=1024,  # Reduced for faster responses
                    stream=True,
                    show_thinking=show_thinking,
                )

            elapsed = time.time() - start_time
            last_raw_output = response

            # Stop loading animation
            stop_event.set()
            loading_thread.join()

            # Add assistant response to history
            session.add_message("assistant", response)

            # Show timing info
            tokens_estimate = len(response.split()) * 1.3  # Rough estimate
            tokens_per_sec = tokens_estimate / elapsed if elapsed > 0 else 0

            print(f"\n{DIM}[{elapsed:.1f}s, ~{tokens_per_sec:.1f} tok/s]{RESET}\n")

        except KeyboardInterrupt:
            stop_event.set()
            loading_thread.join()
            print(f"\n{YELLOW}Generation interrupted{RESET}\n")
            # Remove the user message since we didn't complete
            session.messages.pop()
            session.total_questions -= 1
            continue

        except Exception as e:
            stop_event.set()
            loading_thread.join()
            print(f"\n{YELLOW}Error: {e}{RESET}\n")
            # Remove the user message since we didn't complete
            session.messages.pop()
            session.total_questions -= 1
            continue

    # Save session on exit
    if session.messages:
        save_session_log(session)


def save_session_log(session: ConversationSession):
    """Save the conversation session to a log file."""
    os.makedirs(LOG_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(LOG_DIR, f"session_{ts}.txt")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("# Orin REPL Session\n")
        f.write(f"Timestamp: {ts}\n")
        f.write(f"Duration: {datetime.now() - session.start_time}\n")
        f.write(f"Messages: {len(session.messages)}\n")
        f.write(f"Questions: {session.total_questions}\n\n")

        for msg in session.messages:
            role = msg['role'].capitalize()
            content = msg['content']
            f.write(f"\n{'='*60}\n")
            f.write(f"{role}:\n")
            f.write(f"{'-'*60}\n")
            f.write(f"{content}\n")

    print(f"{DIM}Session saved to {log_path}{RESET}")
