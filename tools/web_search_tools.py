"""
Real-time web search tools for APEX AI Agent.

Primary web search is handled natively by Anthropic's built-in web_search_20250305 tool
— no extra API key required.

This module provides DuckDuckGo-backed utilities for targeted searches:
  - web_search(q)    — DuckDuckGo general search (fallback only).
  - fetch_url(url)   — fetch and clean the text content of any URL.
  - forum_search(q)  — targeted search across Reddit, StackOverflow, HN, dev.to, etc.
  - deep_research(q) — run multiple sub-queries and merge the results.
"""

from __future__ import annotations

import re
import textwrap
import time
from typing import Any

import requests

from utils.logger import log

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}
_TIMEOUT = 15


def _clean_text(html_or_text: str, max_chars: int = 4000) -> str:
    """Strip HTML tags and normalise whitespace."""
    text = re.sub(r"<[^>]+>", " ", html_or_text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


# ─────────────────────────────────────────────
# DUCKDUCKGO SEARCH
# ─────────────────────────────────────────────

def _ddg_search(query: str, num_results: int = 10) -> list[dict]:
    """
    Search via DuckDuckGo (no API key required).
    Returns a list of dicts with: title, url, content (snippet).
    """
    try:
        from duckduckgo_search import DDGS  # type: ignore

        results = []
        with DDGS(timeout=_TIMEOUT) as ddgs:
            for r in ddgs.text(query, max_results=num_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "content": r.get("body", ""),
                        "score": 0.0,
                    }
                )
        log.info(f"DuckDuckGo returned {len(results)} results for: {query[:60]}")
        return results

    except ImportError:
        log.error("duckduckgo-search not installed. Run: pip install duckduckgo-search")
        return []
    except Exception as exc:
        log.error(f"DuckDuckGo search failed: {exc}")
        return []


# ─────────────────────────────────────────────
# PUBLIC: FETCH URL CONTENT
# ─────────────────────────────────────────────

def fetch_url(url: str, max_chars: int = 6000) -> str:
    """
    Fetch the text content of a web page.

    Args:
        url: The URL to fetch.
        max_chars: Maximum characters to return (default 6000).

    Returns:
        Cleaned text content of the page, or an error string.
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "text" not in content_type and "json" not in content_type:
            return f"[Binary content at {url} — cannot display as text]"
        text = _clean_text(resp.text, max_chars=max_chars)
        log.info(f"Fetched {len(text)} chars from {url}")
        return text
    except Exception as exc:
        log.warning(f"fetch_url failed for {url}: {exc}")
        return f"[Failed to fetch {url}: {exc}]"


# ─────────────────────────────────────────────
# PUBLIC: GENERAL WEB SEARCH
# ─────────────────────────────────────────────

def web_search(
    query: str,
    num_results: int = 10,
    fetch_content: bool = True,
    **_kwargs: Any,
) -> str:
    """
    DuckDuckGo-based web search — used as a fallback only.
    Primary web search is handled server-side by Anthropic's web_search_20250305 tool.

    Args:
        query: The search query.
        num_results: Number of results to fetch (default 10).
        fetch_content: If True, try to fetch page body for top 3 results.

    Returns:
        Formatted string of results ready to pass to the model.
    """
    log.info(f"web_search (DDG fallback): '{query}'")

    results = _ddg_search(query, num_results=num_results)
    if not results:
        return f"⚠️ No search results found for: {query}"

    lines: list[str] = [f"## Web Search Results — '{query}' (via DuckDuckGo)\n"]
    for i, r in enumerate(results, 1):
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("content", "")

        if fetch_content and i <= 3 and url:
            fetched = fetch_url(url, max_chars=1500)
            if fetched and not fetched.startswith("[Failed"):
                snippet = fetched

        snippet = textwrap.shorten(snippet, width=800, placeholder="…") if snippet else "(no snippet)"
        lines.append(f"### {i}. {title}\n**URL:** {url}\n{snippet}\n")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# PUBLIC: FORUM & COMMUNITY SEARCH
# ─────────────────────────────────────────────

_FORUM_DOMAINS = [
    "reddit.com",
    "stackoverflow.com",
    "stackexchange.com",
    "news.ycombinator.com",
    "dev.to",
    "medium.com",
    "github.com",
    "github.io",
    "hashnode.dev",
    "community.atlassian.com",
    "discuss.python.org",
    "forums.swift.org",
]


def forum_search(query: str, num_results: int = 10) -> str:
    """
    Search specifically in developer forums and community sites.

    Targets: Reddit, Stack Overflow, Hacker News, dev.to, Medium, GitHub, and more.

    Args:
        query: The search query.
        num_results: Number of results.

    Returns:
        Formatted results string.
    """
    log.info(f"forum_search: '{query}'")

    site_list = " OR ".join(f"site:{d}" for d in _FORUM_DOMAINS[:6])
    enhanced_query = f"{query} ({site_list})"
    results = _ddg_search(enhanced_query, num_results=num_results)
    source = "DuckDuckGo (forums)"

    if not results:
        return f"⚠️ No forum results found for: {query}"

    lines: list[str] = [f"## Forum & Community Results — '{query}' (via {source})\n"]
    for i, r in enumerate(results, 1):
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = textwrap.shorten(
            r.get("content", "(no snippet)"), width=600, placeholder="…"
        )
        lines.append(f"### {i}. {title}\n**URL:** {url}\n{snippet}\n")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# PUBLIC: DEEP RESEARCH (multi-query synthesis)
# ─────────────────────────────────────────────

def deep_research(topic: str) -> str:
    """
    Perform comprehensive research on a topic by running multiple sub-queries,
    including general web, forums, and latest news.

    Args:
        topic: The research topic.

    Returns:
        Combined, labelled results from all sub-searches.
    """
    log.info(f"deep_research: '{topic}'")

    sub_queries = [
        topic,
        f"{topic} tutorial guide how-to",
        f"{topic} best practices tips 2024 2025",
        f"{topic} problems issues solutions",
        f"{topic} reddit stackoverflow community",
    ]

    sections: list[str] = [f"# Deep Research Report: {topic}\n"]
    seen_urls: set[str] = set()

    for q in sub_queries:
        results = _ddg_search(q, num_results=5)
        if not results:
            continue

        sections.append(f"## Query: '{q}'\n")
        added = 0
        for r in results:
            url = r.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            snippet = textwrap.shorten(r.get("content", ""), width=500, placeholder="…")
            sections.append(
                f"**{r.get('title', 'No title')}**\n{url}\n{snippet}\n"
            )
            added += 1
            if added >= 3:
                break

        # Brief pause to be polite to APIs
        time.sleep(0.3)

    sections.append(f"\n---\n*Total unique sources gathered: {len(seen_urls)}*")
    return "\n".join(sections)
