# Ataccama AI Expert 🤖

A Q&A system that uses a local LLM to answer questions about the Ataccama platform based on its official documentation. This project uses a Retrieval-Augmented Generation (RAG) pipeline to provide accurate, context-aware answers.

## Overview

This project automates the process of building a domain-specific AI expert. It involves three main stages:
1.  **Crawling:** A Python script using Playwright fetches the latest Ataccama documentation and saves it as Markdown.
2.  **Data Processing:** The downloaded documents are cleaned and chunked into smaller, meaningful sections for the AI to process.
3.  **Q&A System:** A RAG pipeline uses a local vector database (ChromaDB) and a local LLM (Ollama with Llama 3) to answer user questions based on the processed documentation.

## Features ✨

- **Automated Data Collection:** Crawls the entire Ataccama documentation site.
- **Local First:** Runs entirely on your local machine—no API keys needed.
- **Accurate Answers:** Uses a RAG pipeline to minimize hallucinations and provide fact-based responses.
- **Easy to Use:** Simple command-line interface to ask questions.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/ataccama-ai-expert.git](https://github.com/your-username/ataccama-ai-expert.git)
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

Follow these steps to build the knowledge base and run the expert system.

**Step 1: Crawl the Documentation**
This will download the documentation into the `data/01_raw/` directory.
```bash
python src/tools/crawl.py --start [https://docs.ataccama.com/one/latest/overview.html](https://docs.ataccama.com/one/latest/overview.html) --out ./data/01_raw