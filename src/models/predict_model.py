# ask_expert.py
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# --- 1. Load your processed data ---
print("Loading data...")
documents = []
with open('ataccama_chunks.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        # LangChain works with Document objects, which have page_content and metadata
        from langchain.docstore.document import Document
        doc = Document(page_content=data['content'], metadata={'source': data['source']})
        documents.append(doc)

# --- 2. Create embeddings and store in a vector database ---
print("Creating embeddings and vector store...")
# Use a high-quality, local embedding model
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# ChromaDB is a simple, local vector database
# This will create and store the embeddings in memory
vectorstore = Chroma.from_documents(documents, embedding_model)

# --- 3. Set up the LLM and the RAG chain ---
print("Setting up the RAG chain...")
# Initialize the local LLM you downloaded with Ollama
local_llm = Ollama(model="llama3")

# The retriever's job is to find the most relevant document chunks
retriever = vectorstore.as_retriever()

# We use a prompt template to instruct the LLM on how to answer
prompt_template = """
Answer the question based ONLY on the following context. If the context does not contain the answer, state that you don't know.

Context:
{context}

Question:
{question}
"""
PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

# The RetrievalQA chain combines the retriever and the LLM
qa_chain = RetrievalQA.from_chain_type(
    llm=local_llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": PROMPT}
)

# --- 4. Ask questions! ---
print("\nAtaccama Expert is ready. Type 'exit' to quit.")
while True:
    query = input("\nAsk a question: ")
    if query.lower() == 'exit':
        break
    
    print("Thinking...")
    result = qa_chain.invoke({"query": query})
    print("\nAnswer:\n", result['result'])