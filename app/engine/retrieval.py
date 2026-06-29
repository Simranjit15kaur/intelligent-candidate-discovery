import bm25s
from typing import Any
from langchain_community.vectorstores import FAISS
from tenacity import retry, wait_exponential, stop_after_attempt

from app.db.models import Candidates, Jobs
from app.services.embeddings import embedding_model
from app.config import settings


def flatten_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(flatten_value(v) for v in value if v is not None)
    if isinstance(value, dict):
        return " ".join(flatten_value(v) for v in value.values() if v is not None)
    return str(value)


def candidate_to_text(candidate: Candidates) -> str:
    candidate_dict = candidate.model_dump()
    parts = []
    candidate_fields = [
        "profile_text",
        "skills",
        "years_experience",
        "certifications",
        "raw_data",
    ]
    for field in candidate_fields:
        value = candidate_dict.get(field)
        if value:
            parts.append(flatten_value(value))
    return "\n".join(parts)


def job_to_query(job: Jobs) -> str:
    data = job.model_dump()
    parts = []
    job_fields = [
        "title",
        "description",
        "required_skills",
        "min_experience",
        "required_certs",
    ]
    for field in job_fields:
        value = data.get(field)
        if value:
            parts.append(flatten_value(value))
    return "\n".join(parts)


def reciprocal_rank_fusion(
    bm25_ranking: list[int],       # candidate indices ordered by BM25 rank
    vector_ranking: list[int],     # candidate indices ordered by vector rank
    k: int = 60,                   # RRF constant — 60 is the standard default
) -> dict[int, float]:
    """
    RRF formula: score(idx) = 1/(k + rank_bm25) + 1/(k + rank_vector)
    rank is 1-indexed — best candidate has rank 1.
    Higher RRF score = better candidate.
    """
    rrf_scores: dict[int, float] = {}

    for rank, idx in enumerate(bm25_ranking, start=1):
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (k + rank)

    for rank, idx in enumerate(vector_ranking, start=1):
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (k + rank)

    return rrf_scores


def retrieve(
    candidates: list[Candidates],
    job: Jobs,
    top_k: int = None,
) -> list[dict]:
    if not candidates:
        return []

    top_k = top_k or settings.RETRIEVAL_TOP_K

    candidate_docs = [candidate_to_text(candidate) for candidate in candidates]
    query = job_to_query(job)

    # ── Stage 1A: BM25 ──────────────────────────────────────────────────────
    corpus_tokens = bm25s.tokenize(candidate_docs)
    query_tokens = bm25s.tokenize([query])

    bm25_retriever = bm25s.BM25()
    bm25_retriever.index(corpus_tokens)

    bm25_results, bm25_scores = bm25_retriever.retrieve(
        query_tokens,
        k=len(candidates)
    )

    # bm25_results[0] gives candidate indices ordered best → worst
    bm25_ranking: list[int] = [int(idx) for idx in bm25_results[0]]

    # also keep raw scores for transparency in output
    bm25_score_map: dict[int, float] = {
        int(idx): float(score)
        for idx, score in zip(bm25_results[0], bm25_scores[0])
    }

    # ── Stage 1B: Embedding search via FAISS ────────────────────────────────
    metadatas = [{"candidate_index": i} for i in range(len(candidates))]

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    def build_vectorstore():
        return FAISS.from_texts(
            candidate_docs,
            embedding_model,
            metadatas=metadatas,
        )

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    def embed_query():
        return embedding_model.embed_query(query)

    vectorstore = build_vectorstore()
    query_embedding = embed_query()

    vector_results = vectorstore.similarity_search_with_score_by_vector(
        query_embedding,
        k=len(candidates),
    )

    # vector_results is ordered best → worst (lowest L2 distance first)
    # we only need the ordering for RRF, but also store raw scores
    vector_ranking: list[int] = []
    vector_score_map: dict[int, float] = {}

    for doc, raw_score in vector_results:
        idx = doc.metadata["candidate_index"]
        vector_ranking.append(idx)
        # negate L2 distance so higher = better (for output transparency only)
        vector_score_map[idx] = -float(raw_score)

    # ── Stage 1C: RRF fusion ─────────────────────────────────────────────────
    rrf_scores = reciprocal_rank_fusion(bm25_ranking, vector_ranking, k=60)

    # ── Build final results ──────────────────────────────────────────────────
    final_results = []

    for idx, candidate in enumerate(candidates):
        final_results.append({
            "candidate": candidate,
            "candidate_index": idx,
            "bm25_score": bm25_score_map.get(idx, 0.0),
            "vector_score": vector_score_map.get(idx, 0.0),
            "rrf_score": rrf_scores.get(idx, 0.0),
            # semantic_sim carried forward to features.py
            # normalize vector score to 0-1 range for features.py consumption
            "semantic_sim": None,   # filled below after normalization
        })

    # normalize vector scores to 0–1 for semantic_sim feature in features.py
    raw_v_scores = [r["vector_score"] for r in final_results]
    min_v = min(raw_v_scores)
    max_v = max(raw_v_scores)
    v_range = max_v - min_v if max_v != min_v else 1.0

    for r in final_results:
        r["semantic_sim"] = (r["vector_score"] - min_v) / v_range

    # sort by RRF score descending
    final_results.sort(key=lambda x: x["rrf_score"], reverse=True)

    # assign rank after sorting
    for rank, item in enumerate(final_results, start=1):
        item["rank"] = rank

    # return only top_k
    return final_results[:top_k]