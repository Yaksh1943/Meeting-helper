import os
import pathlib
import pickle
from typing import List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

pathlib.Path("./data").mkdir(exist_ok=True)

INDEX_PATH = "./data/faiss.index"
META_PATH = "./data/faiss_meta.pkl"

# all-MiniLM-L6-v2 is a small, free, local embedding model (no API key,
# no rate limits, ~80MB download on first use). 384-dim output.
EMBED_DIM = 384
_MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def get_model() -> SentenceTransformer:
    """Lazily load the embedding model once per process."""
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_text(text: str) -> np.ndarray:
    """Real semantic embedding, normalized for cosine similarity via inner product."""
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return np.asarray(vec, dtype="float32")


def get_index():
    """
    Load the FAISS index from disk if it matches the current embedding
    dimension. If the file is missing, unreadable, or was built with a
    different embedding model (e.g. the old random-vector placeholder),
    silently start a fresh index rather than crashing.
    """
    if os.path.exists(INDEX_PATH):
        try:
            idx = faiss.read_index(INDEX_PATH)
            if idx.d == EMBED_DIM:
                return idx
        except Exception:
            pass
    return faiss.IndexFlatIP(EMBED_DIM)  # inner product == cosine similarity on normalized vectors


def save_index(index):
    faiss.write_index(index, INDEX_PATH)


def _load_meta() -> dict:
    if os.path.exists(META_PATH):
        with open(META_PATH, "rb") as f:
            return pickle.load(f)
    return {}


def _save_meta(meta: dict):
    with open(META_PATH, "wb") as f:
        pickle.dump(meta, f)


def add_to_index(meeting_id: int, text: str):
    """Embed one chunk of text and add it to the meeting's searchable index."""
    if not text or not text.strip():
        return

    index = get_index()
    vec = embed_text(text)
    index.add(np.array([vec]))
    save_index(index)

    meta = _load_meta()
    meta[len(meta)] = {"meeting_id": meeting_id, "text": text}
    _save_meta(meta)


def query_index(meeting_id: int, question: str, top_k: int = 3) -> List[str]:
    """
    Real semantic search: embed the question, search the whole index,
    then keep only the top_k results that belong to this meeting.

    We search wider than top_k (up to 50 or the full index) because the
    global index holds chunks from every meeting, and the closest global
    matches might not be from the meeting we care about.
    """
    if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
        return []

    index = get_index()
    if index.ntotal == 0:
        return []

    meta = _load_meta()
    vec = embed_text(question)
    search_width = min(50, index.ntotal)
    _, indices = index.search(np.array([vec]), search_width)

    results = []
    for idx in indices[0]:
        if idx == -1:
            continue
        entry = meta.get(int(idx))
        if entry and entry["meeting_id"] == meeting_id:
            results.append(entry["text"])
        if len(results) >= top_k:
            break

    return results