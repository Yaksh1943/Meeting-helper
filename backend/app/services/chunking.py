from typing import List

def chunk_text(text: str, max_len: int = 500) -> List[str]:
    words = text.split()
    chunks = []
    current = []
    for w in words:
        current.append(w)
        if len(current) >= max_len:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks
