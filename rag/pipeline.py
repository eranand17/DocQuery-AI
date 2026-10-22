
from .pdf_processor import extract_text_from_pdf
from .text_splitter import split_text_into_chunks
from .embeddings import load_embedding_model, generate_embeddings
from .vector_store import VectorStore
from .llm import generate_answer
from .web_search import search_web
import re


class RAGPipeline:
    RELEVANCE_THRESHOLD = 0.10
    RETRIEVAL_K = 10
    CONTEXT_K = 5
    SOURCE_K = 3

    STOP_WORDS = {
        "what", "who", "when", "where", "why", "how", "which",
        "the", "is", "are", "was", "were", "a", "an", "and",
        "or", "of", "in", "on", "for", "to", "by", "with",
        "did", "does", "do", "won", "win", "winner", "prize",
        "tell", "me", "about", "please"
    }

    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_model = None

    def _get_embedding_model(self):
        if self.embedding_model is None:
            self.embedding_model = load_embedding_model()
        return self.embedding_model

    @staticmethod
    def _tokens(text):
        return {
            word for word in re.findall(r"[a-z0-9]+", text.lower())
            if len(word) > 1
        }

    def _keyword_overlap(self, question, text):
        question_words = self._tokens(question) - self.STOP_WORDS
        text_words = self._tokens(text)

        if not question_words:
            return 0

        return len(question_words & text_words) / len(question_words)

    def process_pdf(self, pdf_path, document_id):
        pages = extract_text_from_pdf(pdf_path)
        if not pages:
            raise ValueError("No readable text found in this PDF.")

        chunks = split_text_into_chunks(pages)
        if not chunks:
            raise ValueError("No text chunks could be created.")

        model = self._get_embedding_model()
        embeddings = generate_embeddings(
            [chunk["text"] for chunk in chunks], model
        )
        index = self.vector_store.create_index(embeddings)
        self.vector_store.save(index, chunks, document_id)

        return {
            "document_id": document_id,
            "chunk_count": len(chunks),
        }

    def ask_question(self, question, document_ids, top_k=3):
        question = (question or "").strip()
        if not question:
            return {"answer": "Please enter a question.", "sources": []}

        if isinstance(document_ids, (int, str)):
            document_ids = [document_ids]

        retrieved = []

        try:
            model = self._get_embedding_model()
            query_embedding = generate_embeddings([question], model)

            for document_id in document_ids:
                try:
                    index, chunks = self.vector_store.load(document_id)
                    if not chunks:
                        continue

                    results = self.vector_store.search(
                        query_embedding, index, chunks,
                        top_k=min(self.RETRIEVAL_K, len(chunks)),
                        query=question,
                    )

                    for item in results:
                        item = dict(item)
                        item["document_id"] = document_id
                        item["keyword_overlap"] = self._keyword_overlap(
                            question, item.get("text", "")
                        )
                        retrieved.append(item)

                except FileNotFoundError:
                    continue

        except Exception:
            retrieved = []

        retrieved.sort(
            key=lambda item: (
                item["keyword_overlap"],
                item.get("score", 0)
            ),
            reverse=True,
        )

        relevant = [
            item for item in retrieved
            if item.get("score", 0) >= self.RELEVANCE_THRESHOLD
            and item["keyword_overlap"] >= 0.20
        ][:max(self.CONTEXT_K, top_k)]

        if relevant:
            context_items = relevant[:self.CONTEXT_K]
            context = "\n\n".join(
                f"Document ID: {item['document_id']}\n"
                f"Page: {item.get('page', 'Unknown')}\n"
                f"Content: {item['text']}"
                for item in context_items
            )

            try:
                answer = generate_answer(question, context)
            except Exception:
                answer = ""

            if answer and not self._needs_web_fallback(answer):
                sources = []
                seen = set()

                for item in context_items:
                    key = (
                        item["document_id"],
                        item.get("page"),
                        item["text"],
                    )
                    if key in seen:
                        continue

                    seen.add(key)
                    sources.append({
                        "document_id": item["document_id"],
                        "page": item.get("page"),
                        "text": item["text"],
                    })

                    if len(sources) >= self.SOURCE_K:
                        break

                return {"answer": answer, "sources": sources}

        return self._web_fallback(question)

    @staticmethod
    def _needs_web_fallback(answer):
        text = answer.lower().replace("’", "'").replace("‘", "'").strip()

        phrases = (
            "i don't know",
            "i do not know",
            "i cannot answer",
            "i can't answer",
            "cannot answer that question",
            "can't answer that question",
            "i don't have that information",
            "i do not have that information",
            "not provided in the context",
            "not mentioned in the context",
            "not available in the context",
            "context does not contain",
            "context doesn't contain",
            "cannot be determined from the context",
            "can't be determined from the context",
            "insufficient information",
            "information is not available",
            "not found in the provided",
            "not included in the provided document",
            "not included in the provided context",
        )

        return any(phrase in text for phrase in phrases)

    def _web_fallback(self, question):
        try:
            results = search_web(question, max_results=3) or []
        except Exception:
            results = []

        results = [
            item for item in results
            if item.get("title")
            and item.get("url", "").startswith(("https://", "http://"))
            and (item.get("text") or item.get("content") or "").strip()
        ]

        if not results:
            return {
                "answer": (
                    "I couldn't find a reliable answer in the selected PDFs "
                    "or through web search."
                ),
                "sources": [],
            }

        context_parts = []
        for number, item in enumerate(results, start=1):
            content = (item.get("text") or item.get("content") or "").strip()
            context_parts.append(
                f"Source {number}\nTitle: {item['title']}\n"
                f"URL: {item['url']}\nEvidence: {content[:2500]}"
            )

        context = "\n\n".join(context_parts)
        web_question = (
            f"{question}\n\nAnswer every part using the supplied web evidence. "
            "Do not invent facts. If the evidence is insufficient, say so."
        )

        try:
            answer = generate_answer(web_question, context)
        except Exception:
            answer = ""

        if not answer or self._needs_web_fallback(answer):
            answer = (
                "I found web sources, but couldn't generate a reliable answer. "
                "Please review the source excerpts below."
            )

        sources = [
            {
                "title": item["title"],
                "url": item["url"],
                "text": (item.get("text") or item.get("content") or "")[:1500],
            }
            for item in results
        ]

        return {"answer": answer, "sources": sources}


rag_pipeline = RAGPipeline()
