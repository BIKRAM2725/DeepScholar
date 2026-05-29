import faiss
import pickle
INDEX_PATH = "../faiss_output/index_hnsw.faiss"
META_PATH = "../faiss_output/metadata.pkl"
def load_index():
    print("Loading FAISS index...")
    index = faiss.read_index(INDEX_PATH, faiss.IO_FLAG_MMAP)

    print("Loading metadata...")
    with open(META_PATH, "rb") as f:
        metadata = pickle.load(f)

    print(f"Index vectors: {index.ntotal}")
    print(f"Metadata entries: {len(metadata)}")

    return index, metadata