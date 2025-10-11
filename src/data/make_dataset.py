# prepare_data.py
import json
from pathlib import Path

# The directory where your markdown files are stored
input_dir = Path("./ataccama_docs_output")
# The output file for your processed data
output_file = Path("./ataccama_chunks.jsonl")

chunks = []
# Find all markdown files in the directory
for md_file in input_dir.glob("*.md"):
    # The filename (slug) can serve as a source identifier
    source_url_slug = md_file.stem
    
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split the document by major headings (##)
    # This creates more contextually relevant chunks than just splitting by characters.
    # We filter out any empty chunks that might result from the split.
    sections = [section.strip() for section in content.split("\n## ") if section.strip()]
    
    for section_content in sections:
        # Re-add the heading to the chunk content
        chunk_text = "## " + section_content
        
        # Create a dictionary for each chunk
        chunk_data = {
            "source": source_url_slug,
            "content": chunk_text
        }
        chunks.append(chunk_data)

# Save the processed chunks to a JSONL file (one JSON object per line)
with open(output_file, "w", encoding="utf-8") as f:
    for chunk in chunks:
        f.write(json.dumps(chunk) + "\n")

print(f"Processed {len(list(input_dir.glob('*.md')))} files into {len(chunks)} chunks.")
print(f"Output saved to {output_file}")