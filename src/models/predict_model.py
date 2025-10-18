"""
Enhanced Q&A system with persistent vector store, better prompts, and streaming responses.
"""

import json
import logging
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_documents_from_jsonl(data_file: str):
    """Load documents from a JSONL file."""
    documents = []
    data_path = Path(data_file)
    
    if not data_path.exists():
        logger.error(f"Data file does not exist: {data_path}")
        return []
    
    with open(data_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                doc = Document(
                    page_content=data.get('content', ''),
                    metadata={
                        'source': data.get('source', 'unknown'),
                        'chunk_id': data.get('chunk_id', f'line_{line_num}'),
                        'length': data.get('length', len(data.get('content', '')))
                    }
                )
                documents.append(doc)
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing JSON on line {line_num}: {e}")
            except Exception as e:
                logger.warning(f"Error processing line {line_num}: {e}")
    
    logger.info(f"Loaded {len(documents)} documents from {data_file}")
    return documents

def create_vector_store(documents, embedding_model_name, vector_store_path):
    """Create or load a persistent vector store."""
    embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_name)
    
    # Load or create vector store
    vector_store_path = Path(vector_store_path)
    vector_store_path.mkdir(parents=True, exist_ok=True)
    
    if list(vector_store_path.glob("*.parquet")) or list(vector_store_path.glob("chroma.sqlite3*")):
        logger.info(f"Loading existing vector store from {vector_store_path}")
        vectorstore = Chroma(
            persist_directory=str(vector_store_path),
            embedding_function=embedding_model
        )
    else:
        logger.info("Creating new vector store...")
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embedding_model,
            persist_directory=str(vector_store_path)
        )
        logger.info(f"Vector store persisted to {vector_store_path}")
    
    return vectorstore

def get_improved_prompt():
    """Return an improved prompt template for better question answering."""
    prompt_template = """
You are an expert assistant specialized in Ataccama platform documentation. Answer the question based ONLY on the provided context. If the context does not contain the answer, explicitly state that you don't know and do not make up information.

Be concise but comprehensive in your response. If the question involves procedures or steps, list them clearly. When referring to Ataccama components or features, maintain their exact names as they appear in the documentation.

Context:
{context}

Question:
{question}

Provide a helpful and accurate answer based on the context above:
"""
    return PromptTemplate(template=prompt_template, input_variables=["context", "question"])

def main(data_file='./data/02_processed/chunks.jsonl', 
         vector_store_path='./data/03_vector_store',
         model_name='llama3',
         embedding_model_name='all-MiniLM-L6-v2'):
    """Main function to run the Q&A system."""
    
    try:
        # --- 1. Load your processed data ---
        logger.info("Loading data...")
        documents = load_documents_from_jsonl(data_file)
        
        if not documents:
            logger.error("No documents loaded. Please run the processing step first.")
            return
        
        # --- 2. Create or load embeddings and vector store ---
        logger.info("Setting up vector store...")
        vectorstore = create_vector_store(documents, embedding_model_name, vector_store_path)
        
        # --- 3. Set up the LLM and the RAG chain ---
        logger.info("Setting up the RAG chain...")
        
        # Initialize the local LLM
        local_llm = Ollama(model=model_name)
        
        # Configure the retriever with better search parameters
        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 5,  # Retrieve top 5 most relevant chunks
                "score_threshold": 0.5  # Minimum similarity score
            }
        )
        
        # Use the improved prompt template
        prompt = get_improved_prompt()
        
        # Create the QA chain with better configuration
        qa_chain = RetrievalQA.from_chain_type(
            llm=local_llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True  # Include source documents for transparency
        )
        
        # --- 4. Ask questions! ---
        print("\n" + "="*50)
        print("Ataccama Expert is ready. Type 'exit' to quit.")
        print("="*50)
        
        while True:
            try:
                query = input("\nAsk a question: ").strip()
                if query.lower() in ['exit', 'quit', 'q']:
                    break
                
                if not query:
                    print("Please enter a question.")
                    continue
                
                print("Thinking...")
                result = qa_chain.invoke({"query": query})
                
                print(f"\nAnswer:\n{result['result']}")
                
                # Show source information if requested
                if result.get('source_documents'):
                    sources = set(doc.metadata.get('source', 'unknown') for doc in result['source_documents'])
                    print(f"\nSource documents: {', '.join(sources[:3])}")  # Show first 3 sources
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error during query: {e}")
                print("An error occurred. Please try again.")
        
        print("\nThank you for using Ataccama Expert!")
        
    except Exception as e:
        logger.error(f"Error in Q&A system: {e}")
        raise

if __name__ == "__main__":
    main()