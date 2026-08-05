import chromadb
from chromadb.utils import embedding_functions

from app.core.config import CHROMA_DIR, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
collection = _client.get_or_create_collection(name="policy_documents", embedding_function=_embedder, metadata={"hnsw:space": "cosine"})


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    chunks, start = [], 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c.strip() for c in chunks if c.strip()]


def add_document(doc_id: int, title: str, text: str) -> int:
    chunks = chunk_text(text)
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": doc_id, "title": title, "chunk_index": i} for i in range(len(chunks))]
    if chunks:
        collection.add(documents=chunks, ids=ids, metadatas=metadatas)
    return len(chunks)


def search(query: str, top_k: int = TOP_K_RESULTS):
    if collection.count() == 0:
        return []
    results = collection.query(query_texts=[query], n_results=min(top_k, collection.count()))
    hits = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        hits.append({"text": doc, "title": meta.get("title"), "doc_id": meta.get("doc_id"), "score": round(1 - dist, 3)})
    return hits


def total_chunks() -> int:
    return collection.count()
