"""Graph-then-vector retrieval over the authored gold corpus (Master Doc §6).

Pipeline: query → driver-graph lookup (which drivers relate?) → collect those
drivers' doc tags → vector search restricted to chunks sharing a tag → top-k
chunks with stable ids. The graph filter is the differentiator vs. generic RAG:
it injects causal structure into retrieval and keeps citations on-topic.

Two `VectorStore` implementations (decision log D-005):
  MemoryStore — deterministic hashed-bag-of-words embedding, zero deps; used in
                CI and as the automatic fallback.
  ChromaStore — persistent Chroma collection for production (optional extra).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.gold.graph import doc_tags_for, explain_edges, related_drivers

CORPUS_DIR = Path(__file__).parent / "corpus"
_CHUNK_TARGET_WORDS = 90


@dataclass(frozen=True)
class Chunk:
    id: str        # "<doc_id>#<n>" — the citation ref
    doc_id: str
    title: str
    tags: tuple[str, ...]
    text: str


@dataclass
class Retrieved:
    chunk: Chunk
    score: float
    related_nodes: list[str] = field(default_factory=list)


# --- corpus loading ------------------------------------------------------------------

_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _parse_doc(path: Path) -> tuple[str, str, tuple[str, ...], str]:
    raw = path.read_text(encoding="utf-8")
    m = _FRONTMATTER.match(raw)
    if not m:
        raise ValueError(f"corpus doc missing frontmatter: {path.name}")
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    doc_id = meta["id"]
    title = meta["title"].strip('"')
    tags = tuple(t.strip() for t in meta["tags"].strip("[]").split(","))
    body = raw[m.end():].strip()
    return doc_id, title, tags, body


def _chunk_body(body: str) -> list[str]:
    """Paragraph-preserving chunks near the target word count."""
    paras = [p.strip().replace("\n", " ") for p in body.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        candidate = (buf + " " + p).strip()
        if buf and len(candidate.split()) > _CHUNK_TARGET_WORDS * 1.5:
            chunks.append(buf)
            buf = p
        else:
            buf = candidate
    if buf:
        chunks.append(buf)
    return chunks


def load_corpus(corpus_dir: Path | None = None) -> list[Chunk]:
    corpus_dir = corpus_dir or CORPUS_DIR
    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.glob("*.md")):
        doc_id, title, tags, body = _parse_doc(path)
        for i, text in enumerate(_chunk_body(body)):
            chunks.append(Chunk(f"{doc_id}#{i}", doc_id, title, tags, text))
    return chunks


# --- vector stores -------------------------------------------------------------------


class VectorStore(Protocol):
    def add(self, chunks: list[Chunk]) -> None: ...
    def query(self, text: str, k: int, allowed_tags: set[str] | None) -> list[Retrieved]: ...


_TOKEN = re.compile(r"[a-z]{3,}|[0-9]{4}")
_STOP = frozenset([
    "the", "and", "for", "with", "that", "this", "from", "was", "were", "has", "have",
    "are", "but", "not", "its", "into", "over", "when", "than", "then", "they", "their",
    "which", "while", "would", "should", "could", "about", "does", "most", "more",
    "some", "any", "all", "one", "two", "per", "cent", "also", "only", "after",
    "before", "because", "why", "what", "how", "did", "didn",
])


def _stem(tok: str) -> str:
    """Light deterministic stemming: hiking/hiked/hikes → hik."""
    for suffix in ("ing", "ed", "es", "s"):
        if tok.endswith(suffix) and len(tok) - len(suffix) >= 3:
            return tok[: -len(suffix)]
    return tok


def _tokens(text: str) -> list[str]:
    return [_stem(t) for t in _TOKEN.findall(text.lower()) if t not in _STOP]


class MemoryStore:
    """Deterministic TF-IDF cosine retrieval — no model, no network, no deps.

    Accurate enough for a 10-doc curated corpus and, critically for CI,
    perfectly reproducible across machines.
    """

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._tf: list[dict[str, float]] = []
        self._df: dict[str, int] = {}

    def add(self, chunks: list[Chunk]) -> None:
        for c in chunks:
            counts: dict[str, float] = {}
            for tok in _tokens(c.title + " " + c.text):
                counts[tok] = counts.get(tok, 0.0) + 1.0
            self._chunks.append(c)
            self._tf.append(counts)
            for tok in counts:
                self._df[tok] = self._df.get(tok, 0) + 1

    def _idf(self, tok: str) -> float:
        n = len(self._chunks)
        return math.log((n + 1) / (self._df.get(tok, 0) + 1)) + 1.0

    def _vector(self, counts: dict[str, float]) -> dict[str, float]:
        vec = {t: f * self._idf(t) for t, f in counts.items()}
        norm = math.sqrt(sum(w * w for w in vec.values())) or 1.0
        return {t: w / norm for t, w in vec.items()}

    def query(self, text: str, k: int, allowed_tags: set[str] | None) -> list[Retrieved]:
        q_counts: dict[str, float] = {}
        for tok in _tokens(text):
            q_counts[tok] = q_counts.get(tok, 0.0) + 1.0
        q_vec = self._vector(q_counts)
        scored: list[Retrieved] = []
        for chunk, tf in zip(self._chunks, self._tf, strict=True):
            if allowed_tags is not None and not (set(chunk.tags) & allowed_tags):
                continue
            c_vec = self._vector(tf)
            score = sum(w * c_vec.get(t, 0.0) for t, w in q_vec.items())
            scored.append(Retrieved(chunk=chunk, score=round(score, 6)))
        scored.sort(key=lambda r: (-r.score, r.chunk.id))  # deterministic tie-break
        return scored[:k]


class ChromaStore:
    """Persistent Chroma store (requires the `rag` extra)."""

    def __init__(self, path: str) -> None:
        import chromadb  # deferred: optional dependency

        self._client = chromadb.PersistentClient(path=path)
        self._col = self._client.get_or_create_collection("gold_corpus")

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        self._col.upsert(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[{"doc_id": c.doc_id, "title": c.title, "tags": ",".join(c.tags)}
                       for c in chunks],
        )

    def query(self, text: str, k: int, allowed_tags: set[str] | None) -> list[Retrieved]:
        res = self._col.query(query_texts=[text], n_results=max(k * 4, k))
        out: list[Retrieved] = []
        rows = zip(
            res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0],
            strict=True,
        )
        for cid, doc, meta, dist in rows:
            tags = tuple(meta["tags"].split(","))
            if allowed_tags is not None and not (set(tags) & allowed_tags):
                continue
            out.append(Retrieved(
                chunk=Chunk(cid, meta["doc_id"], meta["title"], tags, doc),
                score=round(1.0 - dist, 6),
            ))
        return out[:k]


# --- public API ----------------------------------------------------------------------


@lru_cache(maxsize=1)
def default_store() -> VectorStore:
    """Chroma when installed (prod), memory otherwise (CI/local). Ingests once."""
    store: VectorStore
    try:
        from app.config import settings

        store = ChromaStore(settings.chroma_path)
    except ImportError:
        store = MemoryStore()
    store.add(load_corpus())
    return store


def retrieve(query: str, k: int = 4, store: VectorStore | None = None) -> list[Retrieved]:
    """Graph-then-vector retrieval. Returns chunks with citation-ready ids."""
    nodes = related_drivers(query)
    tags = doc_tags_for(nodes)
    store = store or default_store()
    results = store.query(query, k, allowed_tags=tags or None)
    for r in results:
        r.related_nodes = nodes
    return results


def causal_context(query: str) -> list[dict]:
    """The graph edges relevant to a query — given to the LLM alongside chunks."""
    return explain_edges(related_drivers(query))
