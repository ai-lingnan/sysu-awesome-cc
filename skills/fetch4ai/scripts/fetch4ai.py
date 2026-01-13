#!/usr/bin/env python3
"""
fetch4ai.py - Web content fetching with customizable filtering strategies

Uses crawl4ai to fetch web pages and apply content filters for clean,
LLM-ready markdown output.

Strategies:
  - pruning: Threshold-based noise removal (default)
  - bm25: Query-relevant content extraction
  - tags: HTML tag exclusion with word count filtering
  - composite: Pruning + BM25 for maximum precision

Usage:
  python fetch4ai.py --url "https://example.com" --strategy pruning
  python fetch4ai.py --url "https://example.com" --strategy bm25 --query "machine learning"
  python fetch4ai.py --url "https://example.com" --strategy tags --excluded-tags "nav,footer"
"""

import asyncio
import argparse
import json
import sys
import os
from datetime import datetime
from typing import Optional
from contextlib import contextmanager


@contextmanager
def suppress_output():
    """Context manager to suppress stdout/stderr."""
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "crawl4ai not installed. Run: pip install -U crawl4ai && crawl4ai-setup",
        "error_type": "import_error"
    }))
    sys.exit(1)


async def fetch_with_pruning(
    url: str,
    threshold: float = 0.48,
    min_word_threshold: int = 5,
    word_count_threshold: int = 10,
    excluded_tags: Optional[list] = None,
    include_links: bool = True,
    include_images: bool = False,
    exclude_external_links: bool = False,
    session_id: Optional[str] = None,
    timeout: int = 30,
) -> dict:
    """Fetch with PruningContentFilter for noise removal."""

    pruning_filter = PruningContentFilter(
        threshold=threshold,
        threshold_type="fixed",
        min_word_threshold=min_word_threshold
    )

    markdown_generator = DefaultMarkdownGenerator(
        content_filter=pruning_filter,
        options={
            "include_links": include_links,
            "include_images": include_images,
            "body_width": 0
        }
    )

    browser_config = BrowserConfig(headless=True, java_script_enabled=True)

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=markdown_generator,
        word_count_threshold=word_count_threshold,
        excluded_tags=excluded_tags or [],
        exclude_external_links=exclude_external_links,
        session_id=session_id,
        page_timeout=timeout * 1000  # Convert to milliseconds
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        return process_result(result, url, "pruning")


async def fetch_with_bm25(
    url: str,
    query: str,
    bm25_threshold: float = 1.2,
    word_count_threshold: int = 10,
    excluded_tags: Optional[list] = None,
    include_links: bool = True,
    include_images: bool = False,
    exclude_external_links: bool = False,
    session_id: Optional[str] = None,
    timeout: int = 30,
) -> dict:
    """Fetch with BM25ContentFilter for query-relevant extraction."""

    if not query:
        return {
            "success": False,
            "url": url,
            "error": "BM25 strategy requires --query parameter",
            "error_type": "missing_parameter"
        }

    bm25_filter = BM25ContentFilter(
        user_query=query,
        bm25_threshold=bm25_threshold,
        language="english"
    )

    markdown_generator = DefaultMarkdownGenerator(
        content_filter=bm25_filter,
        options={
            "include_links": include_links,
            "include_images": include_images,
            "body_width": 0
        }
    )

    browser_config = BrowserConfig(headless=True, java_script_enabled=True)

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=markdown_generator,
        word_count_threshold=word_count_threshold,
        excluded_tags=excluded_tags or [],
        exclude_external_links=exclude_external_links,
        session_id=session_id,
        page_timeout=timeout * 1000
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        return process_result(result, url, "bm25", query=query)


async def fetch_with_tags(
    url: str,
    excluded_tags: list,
    word_count_threshold: int = 10,
    include_links: bool = True,
    include_images: bool = False,
    exclude_external_links: bool = False,
    session_id: Optional[str] = None,
    timeout: int = 30,
) -> dict:
    """Fetch with tag exclusion and word count filtering."""

    default_excluded = ["nav", "footer", "header", "aside"]
    tags_to_exclude = excluded_tags if excluded_tags else default_excluded

    markdown_generator = DefaultMarkdownGenerator(
        options={
            "include_links": include_links,
            "include_images": include_images,
            "body_width": 0
        }
    )

    browser_config = BrowserConfig(headless=True, java_script_enabled=True)

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=markdown_generator,
        word_count_threshold=word_count_threshold,
        excluded_tags=tags_to_exclude,
        exclude_external_links=exclude_external_links,
        session_id=session_id,
        page_timeout=timeout * 1000
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        return process_result(result, url, "tags")


async def fetch_composite(
    url: str,
    query: str,
    threshold: float = 0.4,
    bm25_threshold: float = 1.2,
    min_word_threshold: int = 5,
    word_count_threshold: int = 10,
    excluded_tags: Optional[list] = None,
    include_links: bool = True,
    include_images: bool = False,
    exclude_external_links: bool = False,
    session_id: Optional[str] = None,
    timeout: int = 30,
) -> dict:
    """Two-pass filtering: Pruning first, then BM25."""

    if not query:
        return {
            "success": False,
            "url": url,
            "error": "Composite strategy requires --query parameter",
            "error_type": "missing_parameter"
        }

    # First pass: Pruning
    pruning_filter = PruningContentFilter(
        threshold=threshold,
        threshold_type="fixed",
        min_word_threshold=min_word_threshold
    )

    markdown_generator = DefaultMarkdownGenerator(
        content_filter=pruning_filter,
        options={
            "include_links": include_links,
            "include_images": include_images,
            "body_width": 0
        }
    )

    browser_config = BrowserConfig(headless=True, java_script_enabled=True)

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=markdown_generator,
        word_count_threshold=word_count_threshold,
        excluded_tags=excluded_tags or [],
        exclude_external_links=exclude_external_links,
        session_id=session_id,
        page_timeout=timeout * 1000
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)

        if not result.success:
            return {
                "success": False,
                "url": url,
                "error": f"Crawl failed: {result.error_message}",
                "error_type": "crawl_error"
            }

        # Get pruned content
        pruned_content = result.markdown.fit_markdown if hasattr(result.markdown, 'fit_markdown') else result.markdown

        if not pruned_content:
            return {
                "success": False,
                "url": url,
                "error": "No content after pruning pass",
                "error_type": "empty_content"
            }

        # Second pass: BM25 on pruned content
        bm25_filter = BM25ContentFilter(
            user_query=query,
            bm25_threshold=bm25_threshold,
            language="english"
        )

        try:
            bm25_chunks = bm25_filter.filter_content(pruned_content)
            final_content = "\n\n".join(bm25_chunks) if bm25_chunks else pruned_content
        except Exception:
            # If BM25 fails, use pruned content
            final_content = pruned_content

        raw_length = len(result.markdown.raw_markdown) if hasattr(result.markdown, 'raw_markdown') else len(str(result.markdown))
        fit_length = len(final_content)

        return {
            "success": True,
            "url": url,
            "title": getattr(result, 'title', ''),
            "content": final_content,
            "links": extract_links(result),
            "stats": {
                "raw_length": raw_length,
                "fit_length": fit_length,
                "reduction_percent": round((1 - fit_length / raw_length) * 100, 1) if raw_length > 0 else 0
            },
            "strategy": "composite",
            "query": query,
            "metadata": {
                "fetch_time": datetime.now().isoformat(),
                "word_count": len(final_content.split())
            }
        }


def process_result(result, url: str, strategy: str, query: str = None) -> dict:
    """Process crawl result into standardized output format."""

    if not result.success:
        return {
            "success": False,
            "url": url,
            "error": f"Crawl failed: {result.error_message}",
            "error_type": "crawl_error"
        }

    # Get markdown content
    if hasattr(result.markdown, 'fit_markdown'):
        content = result.markdown.fit_markdown
        raw_length = len(result.markdown.raw_markdown)
    else:
        content = str(result.markdown)
        raw_length = len(content)

    if not content or len(content.strip()) == 0:
        return {
            "success": False,
            "url": url,
            "error": "No content after filtering",
            "error_type": "empty_content"
        }

    fit_length = len(content)

    output = {
        "success": True,
        "url": url,
        "title": getattr(result, 'title', ''),
        "content": content,
        "links": extract_links(result),
        "stats": {
            "raw_length": raw_length,
            "fit_length": fit_length,
            "reduction_percent": round((1 - fit_length / raw_length) * 100, 1) if raw_length > 0 else 0
        },
        "strategy": strategy,
        "metadata": {
            "fetch_time": datetime.now().isoformat(),
            "word_count": len(content.split())
        }
    }

    if query:
        output["query"] = query

    return output


def extract_links(result) -> list:
    """Extract links from crawl result."""
    links = []
    if hasattr(result, 'links') and result.links:
        for link in result.links.get('internal', [])[:50]:  # Limit to 50
            links.append({
                "text": link.get('text', ''),
                "href": link.get('href', '')
            })
    return links


async def main():
    parser = argparse.ArgumentParser(
        description="Fetch web content with customizable filtering strategies"
    )

    parser.add_argument("--url", required=True, help="URL to fetch")
    parser.add_argument(
        "--strategy",
        choices=["pruning", "bm25", "tags", "composite"],
        default="pruning",
        help="Filtering strategy (default: pruning)"
    )

    # Pruning options
    parser.add_argument("--threshold", type=float, default=0.48, help="Pruning threshold (0.0-1.0)")
    parser.add_argument("--min-words", type=int, default=5, help="Minimum words per block")

    # BM25 options
    parser.add_argument("--query", help="Search query for BM25 strategy")
    parser.add_argument("--bm25-threshold", type=float, default=0.8, help="BM25 relevance threshold (lower=more results)")

    # Tag options
    parser.add_argument("--excluded-tags", help="Comma-separated tags to exclude")
    parser.add_argument("--word-count-threshold", type=int, default=10, help="Minimum words per content block")

    # Output options
    parser.add_argument("--include-links", action="store_true", default=True, help="Include links")
    parser.add_argument("--include-images", action="store_true", default=False, help="Include images")
    parser.add_argument("--exclude-external-links", action="store_true", default=False, help="Exclude external links")

    # Session
    parser.add_argument("--session-id", help="Session ID for multi-page crawling")

    # Output options
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--format", choices=["json", "markdown", "md"], default="json",
                        help="Output format: json (full metadata) or markdown (content only)")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--quiet", "-q", action="store_true", default=False,
                        help="Suppress crawl4ai status output")

    args = parser.parse_args()

    # Parse excluded tags
    excluded_tags = None
    if args.excluded_tags:
        excluded_tags = [t.strip() for t in args.excluded_tags.split(",")]

    # Execute appropriate strategy
    async def run_strategy():
        if args.strategy == "pruning":
            return await fetch_with_pruning(
                url=args.url,
                threshold=args.threshold,
                min_word_threshold=args.min_words,
                word_count_threshold=args.word_count_threshold,
                excluded_tags=excluded_tags,
                include_links=args.include_links,
                include_images=args.include_images,
                exclude_external_links=args.exclude_external_links,
                session_id=args.session_id,
                timeout=args.timeout
            )
        elif args.strategy == "bm25":
            return await fetch_with_bm25(
                url=args.url,
                query=args.query,
                bm25_threshold=args.bm25_threshold,
                word_count_threshold=args.word_count_threshold,
                excluded_tags=excluded_tags,
                include_links=args.include_links,
                include_images=args.include_images,
                exclude_external_links=args.exclude_external_links,
                session_id=args.session_id,
                timeout=args.timeout
            )
        elif args.strategy == "tags":
            return await fetch_with_tags(
                url=args.url,
                excluded_tags=excluded_tags,
                word_count_threshold=args.word_count_threshold,
                include_links=args.include_links,
                include_images=args.include_images,
                exclude_external_links=args.exclude_external_links,
                session_id=args.session_id,
                timeout=args.timeout
            )
        elif args.strategy == "composite":
            return await fetch_composite(
                url=args.url,
                query=args.query,
                threshold=args.threshold,
                bm25_threshold=args.bm25_threshold,
                min_word_threshold=args.min_words,
                word_count_threshold=args.word_count_threshold,
                excluded_tags=excluded_tags,
                include_links=args.include_links,
                include_images=args.include_images,
                exclude_external_links=args.exclude_external_links,
                session_id=args.session_id,
                timeout=args.timeout
            )

    try:
        if args.quiet:
            with suppress_output():
                result = await run_strategy()
        else:
            result = await run_strategy()
    except asyncio.TimeoutError:
        result = {
            "success": False,
            "url": args.url,
            "error": "Request timed out",
            "error_type": "timeout"
        }
    except Exception as e:
        result = {
            "success": False,
            "url": args.url,
            "error": str(e),
            "error_type": "unknown"
        }

    # Format output
    if args.format in ("markdown", "md"):
        if result.get("success"):
            output_text = result.get("content", "")
        else:
            output_text = f"# Error\n\n{result.get('error', 'Unknown error')}"
    else:
        output_text = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"Output saved to {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    asyncio.run(main())
