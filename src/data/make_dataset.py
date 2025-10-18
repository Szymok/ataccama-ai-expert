"""
Enhanced data processing with better chunking strategies and content cleaning.
"""

import json
import re
from pathlib import Path
import logging
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_markdown_content(content: str) -> str:
    """Clean and normalize markdown content."""
    # Remove extra whitespace and normalize line breaks
    content = re.sub(r'\n\s*\n', '\n\n', content)
    
    # Remove excessive blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Remove leading/trailing whitespace
    content = content.strip()
    
    return content

def chunk_by_headings(content: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Chunk content by headings while respecting character limits."""
    # Split by major headings (h1, h2, h3)
    heading_pattern = r'(\n#{1,3}\s.*?)(?=\n#{1,3}\s|\Z)'
    sections = re.split(heading_pattern, content)
    
    # Group parts together (headings with their content)
    parts = []
    current_part = ""
    
    for section in sections:
        if section.startswith('\n#'):
            if current_part.strip():
                parts.append(current_part)
            current_part = section
        else:
            current_part += section
    
    if current_part.strip():
        parts.append(current_part)
    
    # Now chunk each part if it's too large
    final_chunks = []
    for part in parts:
        if len(part) <= chunk_size:
            final_chunks.append(part.strip())
        else:
            # For oversized parts, split by paragraphs
            sub_chunks = chunk_by_paragraphs(part, chunk_size, overlap)
            final_chunks.extend(sub_chunks)
    
    return final_chunks

def chunk_by_paragraphs(content: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Chunk content by paragraphs."""
    paragraphs = content.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # Check if adding this paragraph would exceed the chunk size
        if len(current_chunk + paragraph) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Add overlap by including part of the last paragraph or content
            if overlap > 0:
                # Take the last 'overlap' characters from the current chunk to create overlap
                if len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + paragraph
                else:
                    current_chunk = current_chunk + paragraph
            else:
                current_chunk = paragraph
        else:
            current_chunk += '\n\n' + paragraph if current_chunk else paragraph
            
        # If current chunk becomes too large, force split
        if len(current_chunk) > chunk_size:
            # Split the current chunk at the chunk_size limit
            while len(current_chunk) > chunk_size:
                chunk = current_chunk[:chunk_size]
                chunks.append(chunk.strip())
                current_chunk = current_chunk[chunk_size - overlap:] if overlap > 0 else current_chunk[chunk_size:]
            
            if len(current_chunk) > 0 and len(current_chunk) < overlap:
                # If remaining content is less than overlap, include it in the next iteration
                continue
    
    # Add the final chunk if it has content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def remove_duplicates(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate chunks based on content similarity."""
    seen_content = set()
    unique_chunks = []
    
    for chunk in chunks:
        # Create a hashable representation of the content for comparison
        content_key = chunk['content'].strip().lower()
        
        # Only consider content longer than 20 characters to avoid removing small snippets
        if len(content_key) > 20 and content_key not in seen_content:
            seen_content.add(content_key)
            unique_chunks.append(chunk)
        elif len(content_key) <= 20:
            # For short content, still add it but with a warning
            unique_chunks.append(chunk)
    
    logger.info(f"Removed {len(chunks) - len(unique_chunks)} duplicate/similar chunks")
    return unique_chunks

def process_document(file_path: Path, chunk_size: int = 1000, overlap: int = 100) -> List[Dict[str, Any]]:
    """Process a single document file into chunks."""
    source_url_slug = file_path.stem
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
        
        # Clean the content
        cleaned_content = clean_markdown_content(raw_content)
        
        # Skip if content is too short
        if len(cleaned_content) < 50:
            logger.warning(f"Skipping {file_path} - content too short: {len(cleaned_content)} chars")
            return []
        
        # Chunk the content using both strategies
        chunks = chunk_by_headings(cleaned_content, chunk_size, overlap)
        
        # Create chunk data with metadata
        chunk_data = []
        for i, chunk_content in enumerate(chunks):
            if len(chunk_content.strip()) > 20:  # Skip very small chunks
                chunk_dict = {
                    "source": source_url_slug,
                    "content": chunk_content,
                    "chunk_id": f"{source_url_slug}_chunk_{i}",
                    "length": len(chunk_content)
                }
                chunk_data.append(chunk_dict)
        
        logger.info(f"Processed {file_path.name} into {len(chunk_data)} chunks")
        return chunk_data
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return []

def main(input_dir: str, output_file: str, chunk_size: int = 1000, chunk_overlap: int = 100):
    """Main function to process all markdown files in a directory."""
    input_path = Path(input_dir)
    output_path = Path(output_file)
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    all_chunks = []
    
    logger.info(f"Processing documents from {input_path}")
    
    # Find all markdown files in the directory
    md_files = list(input_path.glob("*.md"))
    if not md_files:
        logger.warning(f"No markdown files found in {input_path}")
        return
    
    for md_file in md_files:
        chunks = process_document(md_file, chunk_size, chunk_overlap)
        all_chunks.extend(chunks)
    
    # Remove duplicates
    all_chunks = remove_duplicates(all_chunks)
    
    # Save the processed chunks to a JSONL file (one JSON object per line)
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk) + "\n")
    
    logger.info(f"Processed {len(md_files)} files into {len(all_chunks)} unique chunks.")
    logger.info(f"Output saved to {output_path}")
    
    # Print statistics
    if all_chunks:
        lengths = [chunk['length'] for chunk in all_chunks]
        avg_length = sum(lengths) / len(lengths)
        logger.info(f"Average chunk length: {avg_length:.2f} characters")
        logger.info(f"Chunk length range: {min(lengths)} - {max(lengths)} characters")

if __name__ == "__main__":
    # Default parameters for direct execution
    main(
        input_dir="./ataccama_docs_output",
        output_file="./ataccama_chunks.jsonl",
        chunk_size=1000,
        chunk_overlap=100
    )