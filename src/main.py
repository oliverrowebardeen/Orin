"""
Orin Reasoning Engine - Main Entry Point
A compact local reasoning engine that runs entirely from a USB drive.
"""

import typer
import sys
import os
from typing import Optional
from pathlib import Path

# Add src directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import load_config, setup_logging, validate_query
from reasoning import ReasoningEngine
from rag import RAGEngine


app = typer.Typer(
    name="orin",
    help="Orin Reasoning Engine - Advanced local reasoning with Ollama",
    no_args_is_help=True
)


def initialize_orin():
    """Initialize Orin components."""
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config = load_config(str(config_path))
    
    # Setup logging
    logger = setup_logging(config)
    
    # Initialize reasoning engine
    reasoning_engine = ReasoningEngine(config, logger)
    
    # Initialize RAG engine
    rag_engine = RAGEngine(config, logger)
    
    return config, logger, reasoning_engine, rag_engine


@app.command()
def query(
    question: str = typer.Argument(..., help="The question or problem to solve"),
    method: str = typer.Option(
        "cot", 
        "--method", "-m",
        help="Reasoning method: cot (Chain of Thought), sc (Self-Consistency), ir (Interleaved Reasoning)"
    ),
    use_rag: bool = typer.Option(
        False, 
        "--rag", "-r",
        help="Use RAG (Retrieval-Augmented Generation) if enabled"
    )
):
    """
    Process a query using the specified reasoning method.
    """
    try:
        # Initialize Orin
        config, logger, reasoning_engine, rag_engine = initialize_orin()
        
        # Validate query
        if not validate_query(question):
            typer.echo("Error: Please provide a valid question.", err=True)
            raise typer.Exit(1)
        
        # Validate method
        valid_methods = ["cot", "sc", "ir"]
        if method not in valid_methods:
            typer.echo(f"Error: Invalid method '{method}'. Valid methods: {', '.join(valid_methods)}", err=True)
            raise typer.Exit(1)
        
        logger.info("=" * 50)
        logger.info("ORIN REASONING ENGINE STARTED")
        logger.info("=" * 50)
        
        # Apply RAG if requested
        if use_rag:
            augmented_question = rag_engine.query_with_rag(question)
            if augmented_question != question:
                logger.info("Query augmented with RAG context")
                question = augmented_question
        
        # Process query
        typer.echo(f"\n🤖 Orin is thinking using {method.upper()} reasoning...")
        typer.echo(f"📝 Question: {question[:100]}{'...' if len(question) > 100 else ''}")
        typer.echo("-" * 50)
        
        response = reasoning_engine.reason(question, method)
        
        # Display result
        typer.echo("\n💡 ORIN RESPONSE:")
        typer.echo("-" * 50)
        typer.echo(response)
        typer.echo("-" * 50)
        
        logger.info("ORIN REASONING ENGINE COMPLETED")
        logger.info("=" * 50)
        
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def interactive():
    """
    Start interactive reasoning session.
    """
    try:
        # Initialize Orin
        config, logger, reasoning_engine, rag_engine = initialize_orin()
        
        typer.echo("🤖 Welcome to Orin Interactive Reasoning Session")
        typer.echo("Type 'help' for commands, 'quit' to exit")
        typer.echo("-" * 50)
        
        logger.info("Interactive session started")
        
        while True:
            try:
                user_input = typer.prompt("\n💭 Your question", default="", show_default=False).strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    typer.echo("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    typer.echo("Commands:")
                    typer.echo("  help - Show this help")
                    typer.echo("  quit - Exit interactive session")
                    typer.echo("  Any other text will be processed as a question")
                    continue
                
                # Process the question
                logger.info(f"Interactive query: {user_input}")
                typer.echo("\n🤖 Orin is thinking...")
                
                response = reasoning_engine.reason(user_input, "cot")
                
                typer.echo("\n💡 ORIN RESPONSE:")
                typer.echo(response)
                typer.echo("-" * 30)
                
            except KeyboardInterrupt:
                typer.echo("\n👋 Goodbye!")
                break
            except Exception as e:
                typer.echo(f"Error processing query: {e}")
                continue
        
        logger.info("Interactive session ended")
        
    except Exception as e:
        typer.echo(f"Error initializing interactive session: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def status():
    """
    Check Orin system status and configuration.
    """
    try:
        # Initialize Orin
        config, logger, reasoning_engine, rag_engine = initialize_orin()
        
        typer.echo("🤖 ORIN REASONING ENGINE STATUS")
        typer.echo("=" * 40)
        
        # Model info
        model_config = config.get('model', {})
        typer.echo(f"📊 Model: {model_config.get('name', 'Unknown')}")
        typer.echo(f"🌡️  Temperature: {model_config.get('temperature', 'Unknown')}")
        typer.echo(f"📝 Max Tokens: {model_config.get('max_tokens', 'Unknown')}")
        
        # Ollama info
        ollama_config = config.get('ollama', {})
        typer.echo(f"🔗 Ollama URL: {ollama_config.get('base_url', 'Unknown')}")
        
        # Reasoning methods
        reasoning_config = config.get('reasoning', {})
        typer.echo(f"\n🧠 Reasoning Methods:")
        typer.echo(f"  Chain of Thought: {'✅' if reasoning_config.get('chain_of_thought', {}).get('enabled', True) else '❌'}")
        typer.echo(f"  Self-Consistency: {'✅' if reasoning_config.get('self_consistency', {}).get('enabled', True) else '❌'}")
        typer.echo(f"  Interleaved Reasoning: {'✅' if reasoning_config.get('interleaved_reasoning', {}).get('enabled', True) else '❌'}")
        
        # RAG status
        rag_config = config.get('rag', {})
        typer.echo(f"\n📚 RAG: {'✅ Enabled' if rag_config.get('enabled', False) else '❌ Disabled'}")
        
        # Test connection
        typer.echo(f"\n🔍 Testing Ollama connection...")
        try:
            test_response = reasoning_engine.client.generate("Hello", temperature=0.1)
            if test_response and not test_response.startswith("Error"):
                typer.echo("✅ Ollama connection successful")
            else:
                typer.echo("❌ Ollama connection failed")
        except Exception as e:
            typer.echo(f"❌ Ollama connection failed: {e}")
        
    except Exception as e:
        typer.echo(f"Error checking status: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
