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


def chunk_posts(title: str, posts: list[dict], thread_url: str, doc_id: str,
                chunk_size: int = 800, chunk_overlap: int = 80) -> list[dict]:
    """Split each forum post on its own so every chunk keeps its author, time and permalink.

    Each chunk's content starts with the thread title, which gives short posts topical context.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    base_url = thread_url.split("#")[0]

    chunked_docs = []
    for n, post in enumerate(posts):
        post_key = post.get("id") or f"post-{n}"
        for i, piece in enumerate(splitter.split_text(post["content"])):
            chunked_docs.append({
                "content": f"{title}\n{post['author']}: {piece}",
                "metadata": {
                    "id": f"{doc_id}-{post_key}-{i}",
                    "url": f"{base_url}#{post_key}",
                    "thread_url": base_url,
                    "title": title,
                    "author": post["author"],
                    "timestamp": post["timestamp"],
                    "chunk_index": i,
                },
            })
    return chunked_docs
