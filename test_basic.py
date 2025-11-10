#!/usr/bin/env python3
"""
Basic smoke test for Orin to verify all components work.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from src import main
        from src import reasoning
        from src import llamacpp_client
        from src import repl
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_banner():
    """Test that banner can be printed."""
    print("\nTesting banner...")
    try:
        from src.main import print_orin_banner
        print_orin_banner()
        print("✓ Banner printed successfully")
        return True
    except Exception as e:
        print(f"✗ Banner failed: {e}")
        return False

def test_should_show_thinking():
    """Test the should_show_thinking logic."""
    print("\nTesting should_show_thinking...")
    try:
        from src.reasoning import should_show_thinking

        # Simple questions should not show thinking
        assert not should_show_thinking("hi")
        assert not should_show_thinking("hello")
        assert not should_show_thinking("thanks")

        # Complex questions should show thinking
        assert should_show_thinking("What is the attention mechanism in transformers?")
        assert should_show_thinking("Explain how neural networks learn")
        assert should_show_thinking("This is a very long question with many words that should trigger thinking mode")

        print("✓ should_show_thinking works correctly")
        return True
    except Exception as e:
        print(f"✗ should_show_thinking failed: {e}")
        return False

def test_message_builder():
    """Test message building."""
    print("\nTesting message builder...")
    try:
        from src.reasoning import message_builder

        messages = message_builder("What is 2+2?")
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == "What is 2+2?"

        print("✓ Message builder works correctly")
        return True
    except Exception as e:
        print(f"✗ Message builder failed: {e}")
        return False

def test_conversation_session():
    """Test conversation session."""
    print("\nTesting conversation session...")
    try:
        from src.repl import ConversationSession

        session = ConversationSession()
        assert len(session.messages) == 0

        session.add_message("user", "Hello")
        assert len(session.messages) == 1
        assert session.messages[0]['role'] == 'user'

        session.add_message("assistant", "Hi there!")
        assert len(session.messages) == 2

        session.clear_history()
        assert len(session.messages) == 0

        print("✓ Conversation session works correctly")
        return True
    except Exception as e:
        print(f"✗ Conversation session failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Orin Basic Tests")
    print("=" * 60)

    tests = [
        test_imports,
        test_banner,
        test_should_show_thinking,
        test_message_builder,
        test_conversation_session,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n✓ All tests passed! Orin is ready to use.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
