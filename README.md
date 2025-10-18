# Ataccama AI Expert 🤖

A Q&A system that uses a local LLM to answer questions about the Ataccama platform based on its official documentation. This project uses a Retrieval-Augmented Generation (RAG) pipeline to provide accurate, context-aware answers.

## Overview

This project automates the process of building a domain-specific AI expert. It involves three main stages:
1.  **Crawling:** A Python script using Playwright fetches the latest Ataccama documentation and saves it as Markdown.
2.  **Data Processing:** The downloaded documents are cleaned and chunked into smaller, meaningful sections for the AI to process.
3.  **Q&A System:** A RAG pipeline uses a local vector database (ChromaDB) and a local LLM (Ollama with Llama 3) to answer user questions based on the processed documentation.

## Features ✨

- **Automated Data Collection:** Crawls the entire Ataccama documentation site with respect to rate limits.
- **Local First:** Runs entirely on your local machine—no API keys needed.
- **Accurate Answers:** Uses a RAG pipeline to minimize hallucinations and provide fact-based responses.
- **Easy to Use:** Simple command-line interface to ask questions.
- **Persistent Storage:** Vector store is saved to disk for reuse between sessions.
- **Configurable:** Supports customizable parameters for all operations.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/ataccama-ai-expert.git
    cd ataccama-ai-expert
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Install the Playwright browser:**
    ```bash
    python -m playwright install --with-deps chromium
    ```

4.  **Download a local LLM with Ollama:**
    - Install Ollama from [ollama.com](https://ollama.com/).
    - Pull the Llama 3 model:
      ```bash
      ollama pull llama3
      ```

## Usage

The system provides a unified command-line interface with different subcommands for each stage:

**Step 1: Crawl the Documentation**
This will download the documentation into the `data/01_raw/` directory.
```bash
python -m src.cli crawl --start https://docs.ataccama.com/one/latest/overview.html --out ./data/01_raw
```

**Step 2: Process the Raw Data**
This converts the raw markdown files into processed chunks for the RAG system.
```bash
python -m src.cli process --input ./data/01_raw --output ./data/02_processed/chunks.jsonl
```

**Step 3: Run the Q&A System**
This starts the interactive Q&A session with the Ataccama expert.
```bash
python -m src.cli qa
```

### Alternative Direct Method (without CLI)

You can also run each component directly:

**Crawling:**
```bash
python tools/crawl.py --start https://docs.ataccama.com/one/latest/overview.html --out ./data/01_raw
```

**Processing:**
```bash
python src/data/make_dataset.py
```

**Q&A:**
```bash
python src/models/predict_model.py
```

### CLI Options

**Crawling Options:**
```bash
python -m src.cli crawl --start URL [URL ...] --out OUTPUT_DIR [options]
  --max-pages N          Maximum pages to crawl (default: 100)
  --domain DOMAIN        Domain to restrict crawling to (default: docs.ataccama.com)
  --delay SECONDS        Delay between requests (default: 1.0)
```

**Processing Options:**
```bash
python -m src.cli process --input INPUT_DIR --output OUTPUT_FILE [options]
  --chunk-size N         Maximum chunk size in characters (default: 1000)
  --chunk-overlap N      Overlap between chunks (default: 100)
```

**Q&A Options:**
```bash
python -m src.cli qa [options]
  --data FILE            Path to processed chunks file (default: ./data/02_processed/chunks.jsonl)
  --vector-store PATH    Path to vector store directory (default: ./data/03_vector_store)
  --model NAME           Ollama model to use (default: llama3)
  --embedding-model NAME Embedding model to use (default: all-MiniLM-L6-v2)
```

## Project Structure

```
ataccama-ai-expert/
├── data/                 # Data directory (following cookiecutter-data-science)
│   ├── 01_raw/          # Raw crawled markdown files
│   ├── 02_processed/    # Processed chunks in JSONL format
│   └── 03_vector_store/ # Persistent vector store
├── src/                 # Source code
│   ├── cli.py           # Command line interface
│   ├── data/            # Data processing modules
│   ├── models/          # Model and Q&A system
│   └── ...
├── tools/               # Standalone tools
│   └── crawl.py         # Web crawling functionality
├── requirements.txt     # Python dependencies
├── Makefile            # Make targets for common operations
└── README.md           # This file
```

## Makefile Commands

The project includes a Makefile with convenient commands:

```bash
# Setup the environment
make setup

# Run the complete pipeline
make run-all

# Run each step separately
make crawl
make process
make qa

# Clean data directories
make clean
```

## Troubleshooting

- **If Ollama is not running**: Make sure the Ollama service is started before running the Q&A system.
- **If crawling fails**: Check your internet connection and ensure the target domain is accessible.
- **For memory issues**: Process smaller batches or use a machine with more RAM.