"""Document processing + retrieval (the 'R' in RAG).

Teacher notes (PDF/TXT) are split into overlapping chunks and indexed with TF-IDF.
Retrieval finds the passages most relevant to a question or rubric criterion so the
evaluation is grounded in the actual course material.
"""
import io
import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Chunk:
    source: str
    index: int
    text: str


def read_pdf(data: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def load_document(name: str, data: bytes) -> str:
    if name.lower().endswith(".pdf"):
        return read_pdf(data)
    return data.decode("utf-8", errors="ignore")


def chunk_text(text: str, source: str, chunk_words: int = 120, overlap: int = 30):
    words = re.sub(r"\s+", " ", text).strip().split(" ")
    words = [w for w in words if w]
    if not words:
        return []
    step = max(chunk_words - overlap, 1)
    chunks = []
    for i, start in enumerate(range(0, len(words), step)):
        piece = words[start:start + chunk_words]
        if len(piece) < 15 and chunks:      # skip tiny tail, already covered by overlap
            break
        chunks.append(Chunk(source=source, index=len(chunks) + 1, text=" ".join(piece)))
        if start + chunk_words >= len(words):
            break
    return chunks


class Retriever:
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self._ready = False
        if self.chunks:
            self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            self.matrix = self.vectorizer.fit_transform([c.text for c in self.chunks])
            self._ready = True

    def search(self, query: str, k: int = 3, min_score: float = 0.05):
        if not self._ready or not query.strip():
            return []
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [(self.chunks[i], float(scores[i])) for i in ranked if scores[i] >= min_score]
