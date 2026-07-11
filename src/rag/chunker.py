from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_document(text: str, metadata: dict, chunk_size: int = 500, chunk_overlap: int = 50) -> list[dict]:
    """Split text into smaller chunks while preserving metadata.
    
    Each returned chunk is a dict:
    {
        "content": str,
        "metadata": dict  # copy of original metadata with chunk_index and chunk-specific id added
    }
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = splitter.split_text(text)
    
    chunked_docs = []
    for i, chunk in enumerate(chunks):
        chunk_meta = metadata.copy()
        chunk_meta["chunk_index"] = i
        # Ensure we construct a unique ID for this specific chunk
        base_id = metadata.get("id", "doc")
        chunk_meta["id"] = f"{base_id}-chunk-{i}"
        chunked_docs.append({
            "content": chunk,
            "metadata": chunk_meta
        })
    return chunked_docs
