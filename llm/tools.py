
import os

import requests
from langchain_core.tools import tool
from tools.reranker import rerank_results
import trafilatura


SEARXNG_URL = os.getenv(
    "SEARXNG_URL",
    "http://localhost:8080/search",
)


from typing import Literal

import requests
from langchain_core.tools import tool

MAX_RESULTS = 5
SNIPPET_CHARS = 400


def _search_searxng(query: str, time_range: str) -> list[dict]:
    params = {"q": query, "format": "json", "language": "en", "safesearch": 1}
    if time_range != "any":
        params["time_range"] = time_range
    r = requests.get(SEARXNG_URL, params=params, timeout=15)
    r.raise_for_status()
    return [
        {
            "title": x.get("title", ""),
            "url": x.get("url", ""),
            "content": x.get("content", ""),
            "date": x.get("publishedDate"),
        }
        for x in r.json().get("results", [])
    ]


def _search_ddgs(query: str, time_range: str) -> list[dict]:
    from ddgs import DDGS

    timelimit = {"day": "d", "week": "w", "month": "m", "year": "y"}.get(time_range)
    return [
        {
            "title": x.get("title", ""),
            "url": x.get("href", ""),
            "content": x.get("body", ""),
            "date": None,
        }
        for x in DDGS().text(query, max_results=20, timelimit=timelimit)
    ]


@tool
def web_search(
    query: str,
    time_range: Literal["any", "day", "week", "month", "year"] = "any",
) -> str:
    """Search the web for current or external information.

    Args:
        query: A short, specific search query with the key names and topic.
        time_range: Restrict to recent results. Use "day" or "week" for news,
            scores and breaking events, "month" or "year" for recent releases,
            and "any" otherwise.
    """
    try:
        results = _search_searxng(query, time_range)
    except requests.RequestException:
        try:
            results = _search_ddgs(query, time_range)
        except Exception as e:
            return (
                f"Search failed ({type(e).__name__}). "
                "Tell the user you could not verify this."
            )

    # Drop duplicates and results with no snippet
    seen, unique = set(), []
    for r in results:
        if r["url"] and r["content"].strip() and r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    if not unique:
        return "No results found. Try different wording, or tell the user you could not verify this."

    try:
        ranked = rerank_results(query=query, results=unique[:20], top_k=MAX_RESULTS)
    except Exception:
        ranked = unique[:MAX_RESULTS]  # reranker failed, keep search-engine order

    blocks = []
    for r in ranked:
        date = f"\nDate: {r['date']}" if r.get("date") else ""
        blocks.append(
            f"Title: {r['title']}\n"
            f"URL: {r['url']}{date}\n"
            f"Snippet: {r['content'][:SNIPPET_CHARS]}"
        )
    return "\n\n".join(blocks)

@tool
def read_page(url: str) -> str:
    """Open a web page and return its main text. Use after web_search when
    a snippet is not enough (schedules, tables, articles, documentation)."""
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        text = trafilatura.extract(
            r.text, include_tables=True, include_links=False
        )
    except Exception as e:
        return f"Could not read the page ({type(e).__name__})."
    if not text:
        return "The page had no readable text (it may need JavaScript)."
    return text[:6000]
