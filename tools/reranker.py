from FlagEmbedding import FlagReranker

reranker = FlagReranker(
    "BAAI/bge-reranker-v2-m3",
    use_fp16=False,
)

def rerank_results(
    query: str,
    results: list[dict],
    top_k: int = 20,
):
    if not results:
        return []

    pairs = [
        [
            query,
            (
                f"Title: {r.get('title', '')}\n"
                f"Content: {r.get('content', r.get('snippet', ''))}"
            ),
        ]
        for r in results
    ]

    scores = reranker.compute_score(pairs)

    ranked = sorted(
        zip(results, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    return [
        {**result, "rerank_score": float(score)}
        for result, score in ranked[:top_k]
    ]