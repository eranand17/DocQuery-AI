from sentence_transformers import SentenceTransformer
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
def load_embedding_model():
    """
    Load the pre-trained sentence embedding model.
    """
    return SentenceTransformer(MODEL_NAME)
def generate_embeddings(texts, model):
    """
    Convert text chunks into numerical vectors.

    Args:
        texts (list): List of text strings.
        model: Loaded sentence transformer model.

    Returns:
        numpy.ndarray: Generated embedding vectors.
    """
    return model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
