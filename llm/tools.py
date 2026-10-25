
import os

import requests
from langchain_core.tools import tool
from tools.reranker import rerank_results


SEARXNG_URL = os.getenv(
    "SEARXNG_URL",
    "http://localhost:8080/search",
)


@tool
def web_search(query: str) -> str:
    """Search the web for current information, technical documentation,
    programming solutions, or other external information. Prioritize recent sources when getting
    information.

    Args:
        query: A concise web search query.
    """
    try:
        response = requests.get(
            SEARXNG_URL,
            params={
                "q": query,
                "format": "json",
                "language": "en",
                "safesearch": 1,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])

        # Score all candidates, then keep the most relevant five
        ranked_results = rerank_results(
            query=query,
            results=results[:20],
            top_k=20,
        )

        formatted_results = []

        for result in ranked_results:
            formatted_results.append(
                f"Title: {result.get('title', 'Untitled')}\n"
                f"URL: {result.get('url', '')}\n"
                f"Relevance: {result['rerank_score']:.3f}\n"
                f"Snippet: {result.get('content', '')}"
            )

        return "\n\n".join(formatted_results)

    except requests.RequestException as exc:
        return f"Web search failed: {exc}"
    except ValueError:
        return "Web search failed: SearXNG returned invalid JSON."