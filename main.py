import argparse
import logging
import sys

from src.graph.graph import build_graph
from src.rag.core import reset_collection
from src.log_config import setup_logging

logger = logging.getLogger(__name__)



def main(args: list[str] = None) -> None:
    """CLI entry point parsing arguments and orchestrating task execution."""
    parser = argparse.ArgumentParser(
        description="RAG + Scraping tool for Voz forums"
    )
    
    # Global flags
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Reset/clear the ChromaDB vector database collection"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )

    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    # 'ask' subcommand
    ask_parser = subparsers.add_parser(
        "ask",
        help="Ask a question and optionally scrape a thread"
    )
    ask_parser.add_argument(
        "question",
        type=str,
        help="The question to ask the system"
    )
    ask_parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Direct URL of the Voz forum thread to scrape"
    )
    
    # Parse the arguments
    parsed_args = parser.parse_args(args)
    
    # Initialize logging configuration based on verbose flag
    setup_logging(verbose=parsed_args.verbose)

    
    # Handle --reset-db
    if parsed_args.reset_db:
        logger.info("Resetting ChromaDB collection...")
        reset_collection()
        print("Database reset successfully.")
        return
        
    # Handle 'ask' subcommand
    if parsed_args.command == "ask":
        logger.info("Initializing LangGraph workflow...")
        app = build_graph()
        
        initial_state = {
            "question": parsed_args.question,
            "loop_count": 0,
            "url": parsed_args.url,
            "retrieved_context": None,
            "answer": None,
            "route_decision": None
        }
        
        logger.info("Invoking graph execution pipeline...")
        from src.observability import get_langfuse_callback
        handler = get_langfuse_callback()
        config = {"callbacks": [handler]} if handler else {}
        final_state = app.invoke(initial_state, config=config)

        
        answer = final_state.get("answer") or "Could not generate an answer."
        print("\n=== ANSWER ===")
        print(answer)
        print("==============\n")
        return
        
    # If no arguments provided, show help
    parser.print_help()


if __name__ == "__main__":
    main()
