import os 
import faiss
import numpy as np
import pickle

INDEX_PATH = "./data/faiss.index"
META_PATH = "./data/faiss_meta.pkl"

def get_index():
    if os.path.exists(INDEX_PATH):
        return faiss.read_index(INDEX_PATH)
    return faiss.IndexFlatL2(1536)


def save_index(index):
    faiss.write_index(index, INDEX_PATH)


def add_to_index(meeting_id: int, text: str):
    index = get_index()
    vec = embed_text(text)
    index.add(np.array([vec]).astype("float32"))
    save_index(index)
    meta = {}
    if os.path.exists(META_PATH):
        with open(META_PATH, "rb") as f:
            meta = pickle.load(f)
    meta[len(meta)] = {"meeting_id": meeting_id, "text": text}
    with open(META_PATH, "wb") as f:
        pickle.dump(meta, f)    


def query_index(meeting_id: int, question: str) -> str:
    if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
        return ""
    index = get_index()
    vec = embed_text(question)
    D, I = index.search(np.array([vec]).astype("float32"), 1)
    with open(META_PATH, "rb") as f:
        meta = pickle.load(f)
    if I[0][0] in meta:
        entry = meta[I[0][0]]
        if entry["meeting_id"] == meeting_id:
            return entry["text"]
    return ""


def embed_text(text: str):
    if os.getenv("OPENAI_API_KEY"):
        # placeholder embedding
        return np.random.rand(1536)
    # fallback embedding: hash to vector
    np.random.seed(abs(hash(text)) % (2**32))
    return np.random.rand(1536)
