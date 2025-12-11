"""
PyRAG - Main Entry Point

Used to run different modes from command line.
"""

import sys
import argparse
from pathlib import Path

from loguru import logger
from src.utils import get_settings, setup_logger, ensure_directories
from src.ingestion import DocumentIngestion
from src.query_engine import QueryEngine
from src.api import start_server


def launch_gui():
    """Launch GUI application"""
    try:
        import app_gui
        app_gui.main()
    except ImportError as e:
        logger.error(f"Failed to import GUI: {e}")
        print("❌ GUI dependencies not installed.")
        print("💡 Run: pip install customtkinter pillow")
        sys.exit(1)
    except Exception as e:
        logger.error(f"GUI error: {e}")
        print(f"❌ GUI error: {e}")
        sys.exit(1)


def cmd_ingest(args):
    """
    Index documents
    
    Usage:
        python main.py ingest
        python main.py ingest --force
        python main.py ingest --file "my_doc.pdf"
    """
    logger.info("=" * 60)
    logger.info("ETL Pipeline - Document Indexing")
    logger.info("=" * 60)
    
    target_files = None
    if args.file:
        from pathlib import Path
        from src.utils import get_settings
        settings = get_settings()
        file_path = Path(settings.data_dir) / args.file
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            sys.exit(1)
        target_files = [file_path]
    
    ingestion = DocumentIngestion()
    index = ingestion.ingest_documents(force_reindex=args.force, target_files=target_files)
    
    if index:
        stats = ingestion.get_index_stats()
        logger.success("✅ Indexing completed!")
        logger.info(f"📊 Statistics: {stats}")
    else:
        logger.error("❌ Indexing failed!")
        sys.exit(1)


def cmd_query(args):
    """
    Ask a question from command line
    
    Usage:
        python main.py query "What is the current for 2.5mm cable?"
    """
    if not args.question:
        logger.error("❌ Please enter a question!")
        logger.info("💡 Usage: python main.py query 'Your question'")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Query Engine - Q&A")
    logger.info("=" * 60)
    
    engine = QueryEngine()
    result = engine.query(args.question, return_sources=True)
    
    # Display results
    print("\n" + "=" * 60)
    print(f"❓ QUESTION: {args.question}")
    print("=" * 60)
    print(f"\n✅ ANSWER:\n{result['answer']}\n")
    
    if result['sources']:
        print("=" * 60)
        print("📚 SOURCES:")
        print("=" * 60)
        for source in result['sources']:
            print(f"\n[{source['rank']}] {source['metadata'].get('file_name', 'Unknown')}")
            print(f"    Page: {source['metadata'].get('page_label', '?')}")
            if source['score']:
                print(f"    Similarity: {source['score']:.3f}")
            print(f"    {source['text'][:200]}...")


def cmd_interactive(args):
    """
    Interactive Q&A mode
    
    Usage:
        python main.py interactive
    """
    logger.info("=" * 60)
    logger.info("Interactive Mode - Type your questions (type 'exit' to quit)")
    logger.info("=" * 60)
    
    engine = QueryEngine()
    
    print("\n🤖 PyRAG Assistant ready! You can start asking questions.\n")
    
    while True:
        try:
            question = input("\n❓ Question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['exit', 'quit']:
                print("\n👋 Goodbye!")
                break
            
            # Process question
            result = engine.query(question, return_sources=True)
            
            print(f"\n✅ Answer:\n{result['answer']}\n")
            
            # Show sources briefly
            if result['sources']:
                print(f"📚 Sources: {len(result['sources'])} document(s) used")
                for source in result['sources'][:3]:  # Show first 3
                    print(f"  • {source['metadata'].get('file_name')} - "
                          f"Page {source['metadata'].get('page_label')}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")


def cmd_serve(args):
    """
    Start FastAPI server
    
    Usage:
        python main.py serve
    """
    logger.info("=" * 60)
    logger.info("Starting API Server")
    logger.info("=" * 60)
    
    start_server()


def cmd_stats(args):
    """
    Show index statistics
    
    Usage:
        python main.py stats
    """
    logger.info("=" * 60)
    logger.info("Index Statistics")
    logger.info("=" * 60)
    
    try:
        ingestion = DocumentIngestion()
        stats = ingestion.get_index_stats()
        
        print("\n📊 Database Information:")
        print("=" * 60)
        print(f"Collection: {stats.get('collection_name')}")
        print(f"Total Nodes: {stats.get('total_nodes')}")
        print(f"Database Path: {stats.get('db_path')}")
        print(f"Metadata: {stats.get('metadata')}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Could not retrieve statistics: {e}")
        logger.warning("💡 Index documents first with 'python main.py ingest'")


def main():
    """Main function - CLI parser"""
    parser = argparse.ArgumentParser(
        description="PyRAG - Engineering Standards RAG Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py gui                                 # Launch GUI (recommended)
  python main.py ingest                              # Index documents
  python main.py ingest --force                      # Rebuild index from scratch
  python main.py query "Cable current capacity?"     # Ask single question
  python main.py interactive                         # Interactive mode
  python main.py serve                               # Start API server
  python main.py stats                               # Show statistics
        """
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # gui command (default)
    parser_gui = subparsers.add_parser('gui', help='Launch GUI application (default)')
    parser_gui.set_defaults(func=lambda args: launch_gui())
    
    # ingest command
    parser_ingest = subparsers.add_parser('ingest', help='Index documents')
    parser_ingest.add_argument(
        '--force', 
        action='store_true',
        help='Delete existing index and rebuild from scratch'
    )
    parser_ingest.add_argument(
        '--file',
        type=str,
        help='Specific file to ingest (relative to data/ folder)'
    )
    parser_ingest.set_defaults(func=cmd_ingest)
    
    # query command
    parser_query = subparsers.add_parser('query', help='Ask a single question')
    parser_query.add_argument(
        'question',
        type=str,
        nargs='?',
        help='Your question'
    )
    parser_query.set_defaults(func=cmd_query)
    
    # interactive command
    parser_interactive = subparsers.add_parser('interactive', help='Interactive Q&A')
    parser_interactive.set_defaults(func=cmd_interactive)
    
    # serve command
    parser_serve = subparsers.add_parser('serve', help='Start API server')
    parser_serve.set_defaults(func=cmd_serve)
    
    # stats command
    parser_stats = subparsers.add_parser('stats', help='Index statistics')
    parser_stats.set_defaults(func=cmd_stats)
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command provided, launch GUI by default
    if not args.command:
        logger.info("No command specified, launching GUI...")
        launch_gui()
        return
    
    # Setup logger
    settings = get_settings()
    setup_logger(settings.log_level)
    
    # Ensure required directories exist
    ensure_directories()
    
    # Run the relevant command
    args.func(args)


if __name__ == "__main__":
    main()
