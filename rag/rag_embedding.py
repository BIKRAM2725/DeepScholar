from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_query(query: str) -> np.ndarray:
    """
    Generate a vector for the query using
    sentence-transformers/all-MiniLM-L6-v2.
    Returns a normalized float32 vector (1,384).
    """

    global model

    if not query or not query.strip():
        return None

    vector = model.encode(
        [query],
        normalize_embeddings=True,
        show_progress_bar=False
    )

    return vector.astype(np.float32)



