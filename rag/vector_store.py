
from pathlib import Path
import re

import faiss
import numpy as np
from django.conf import settings


class VectorStore:
    """Manage FAISS indexes and hybrid text retrieval."""

    def __init__(self):
        self.storage_path = Path(settings.BASE_DIR) / "vector_data"
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def create_index(self, embeddings):
        embeddings = np.asarray(embeddings, dtype=np.float32)

        if embeddings.ndim != 2 or embeddings.shape[0] == 0:
            raise ValueError("Embeddings must be a non-empty 2D array.")

        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        return index

    def save(self, index, chunks, document_id):
        faiss.write_index(index, str(self._index_path(document_id)))
        np.save(self._chunks_path(document_id), chunks, allow_pickle=True)

    def load(self, document_id):
        index_path = self._index_path(document_id)
        chunks_path = self._chunks_path(document_id)

        if not index_path.exists() or not chunks_path.exists():
            raise FileNotFoundError(
                f"Vector store not found for document ID: {document_id}"
            )

        index = faiss.read_index(str(index_path))
        chunks = np.load(chunks_path, allow_pickle=True).tolist()
        return index, chunks

    @staticmethod
    def _tokenize(text):
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be",
            "been", "being", "do", "does", "did", "what", "which",
            "who", "when", "where", "how", "why", "in", "on", "at",
            "of", "to", "for", "and", "or", "with", "from", "by",
            "it", "this", "that", "their", "they", "you", "your",
            "me", "my", "include", "includes", "included",
        }
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return {word for word in words if word not in stop_words}

    
    def search(self, query_embedding, index, chunks, top_k=3, query=""):
        """Rank answer-bearing chunks above question-only chunks."""
        if index.ntotal == 0 or not chunks:
            return []

        query_embedding = np.asarray(
            query_embedding, dtype=np.float32
        ).reshape(1, -1)

        if query_embedding.shape[1] != index.d:
            raise ValueError("Query embedding dimension does not match index.")

        scores, indices = index.search(query_embedding, index.ntotal)
        query_words = self._tokenize(query)
        results = []

        for score, chunk_index in zip(scores[0], indices[0]):
            if chunk_index < 0 or chunk_index >= len(chunks):
                continue

            chunk = chunks[chunk_index]
            text = chunk.get("text", "")
            words = self._tokenize(text)
            overlap = (
                len(query_words & words) / len(query_words)
                if query_words else 0.0
            )

            lines = [line.strip() for line in text.splitlines() if line.strip()]
            question_lines = sum(
                1 for line in lines
                if line.endswith("?") or (
                    re.match(r"^\d+[\.\)]\s", line) and "?" in line
                )
            )
            question_ratio = question_lines / max(len(lines), 1)
            penalty = 0.35 if question_ratio >= 0.6 else 0.0

            semantic_score = float(score)
            combined_score = (
                0.75 * semantic_score + 0.25 * overlap - penalty
            )

            results.append({
                "page": chunk["page"],
                "text": text,
                "score": combined_score,
                "semantic_score": semantic_score,
                "keyword_score": overlap,
            })

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:min(max(1, top_k), len(results))]


    def _index_path(self, document_id):
        return self.storage_path / f"document_{document_id}.faiss"

    def _chunks_path(self, document_id):
        return self.storage_path / f"document_{document_id}_chunks.npy"
