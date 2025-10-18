"""Command Line Interface for Ataccama AI Expert"""

import argparse
import sys
from pathlib import Path
import logging
import yaml

# Add the tools directory to the path so we can import the modules
sys.path.append(str(Path(__file__).parent.parent / 'tools'))

def setup_logging():
    """Setup logging configuration"""
    # Try to load configuration from YAML file
    config_path = Path(__file__).parent.parent / 'logging.conf.yaml'
    if config_path.exists():
        import logging.config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        # Fallback to basic configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ataccama_expert.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

def main():
    parser = argparse.ArgumentParser(
        description='Ataccama AI Expert - A RAG-based Q&A system for Ataccama documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s crawl --start https://docs.ataccama.com/one/latest/overview.html --out ./data/01_raw
  %(prog)s process --input ./data/01_raw --output ./data/02_processed/chunks.jsonl
  %(prog)s qa
        """
    )
    
    setup_logging()
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True

    # Crawl subcommand
    crawl_parser = subparsers.add_parser('crawl', help='Crawl Ataccama documentation')
    crawl_parser.add_argument(
        '--start', 
        nargs='+', 
        required=True, 
        help="Seed URLs under https://docs.ataccama.com"
    )
    crawl_parser.add_argument(
        '--out', 
        required=True, 
        help="Output directory for Markdown files"
    )
    crawl_parser.add_argument(
        '--max-pages', 
        type=int, 
        default=100, 
        help="Maximum pages to crawl (default: 100)"
    )
    crawl_parser.add_argument(
        '--domain', 
        default="docs.ataccama.com",
        help="Domain to restrict crawling to (default: docs.ataccama.com)"
    )
    crawl_parser.add_argument(
        '--delay', 
        type=float, 
        default=1.0, 
        help="Delay between requests in seconds (default: 1.0)"
    )

    # Process subcommand
    process_parser = subparsers.add_parser('process', help='Process Markdown files into chunks')
    process_parser.add_argument(
        '--input', 
        required=True, 
        help="Input directory containing Markdown files"
    )
    process_parser.add_argument(
        '--output', 
        required=True, 
        help="Output file for processed chunks (JSONL format)"
    )
    process_parser.add_argument(
        '--chunk-size', 
        type=int, 
        default=1000, 
        help="Maximum chunk size in characters (default: 1000)"
    )
    process_parser.add_argument(
        '--chunk-overlap', 
        type=int, 
        default=100, 
        help="Overlap between chunks in characters (default: 100)"
    )

    # QA subcommand
    qa_parser = subparsers.add_parser('qa', help='Start the Q&A system')
    qa_parser.add_argument(
        '--data', 
        default='./data/02_processed/chunks.jsonl',
        help="Path to processed chunks file (default: ./data/02_processed/chunks.jsonl)"
    )
    qa_parser.add_argument(
        '--vector-store', 
        default='./data/03_vector_store',
        help="Path to persistent vector store directory (default: ./data/03_vector_store)"
    )
    qa_parser.add_argument(
        '--model', 
        default='llama3',
        help="Ollama model to use (default: llama3)"
    )
    qa_parser.add_argument(
        '--embedding-model', 
        default='all-MiniLM-L6-v2',
        help="Embedding model to use (default: all-MiniLM-L6-v2)"
    )

    # Parse arguments
    args = parser.parse_args()

    if args.command == 'crawl':
        from tools.crawl import main as crawl_main
        import asyncio
        try:
            asyncio.run(crawl_main(
                start_urls=args.start, 
                out_dir=args.out, 
                max_pages=args.max_pages,
                allowed_host=args.domain,
                delay=args.delay
            ))
        except Exception as e:
            logging.error(f"Error during crawling: {e}")
            sys.exit(1)
    
    elif args.command == 'process':
        from src.data.make_dataset import main as process_main
        try:
            process_main(
                input_dir=args.input,
                output_file=args.output,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap
            )
        except Exception as e:
            logging.error(f"Error during processing: {e}")
            sys.exit(1)
    
    elif args.command == 'qa':
        from src.models.predict_model import main as qa_main
        try:
            qa_main(
                data_file=args.data,
                vector_store_path=args.vector_store,
                model_name=args.model,
                embedding_model_name=args.embedding_model
            )
        except Exception as e:
            logging.error(f"Error during Q&A: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()