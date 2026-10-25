from sentence_transformers import CrossEncoder

# Loaded once
reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

def rerank_results(query: str, results: list[dict], top_k: int = 5):
    if not results:
        return []

    pairs = [
        (
            query,
            f"Title: {r.get('title', '')}\n"
            f"Content: {r.get('content', '')}"
        )

        for r in results
    ]

    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(results, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    return [
        {**result, "rerank_score": float(score)}
        for result, score in ranked[:top_k]
    ]