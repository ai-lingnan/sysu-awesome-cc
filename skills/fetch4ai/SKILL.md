---
name: fetch4ai
description: MUST USE THIS SKILL when the user asks or an agent needs to "fetch web content", "crawl a page", "use crawl4ai", "extract content from URL", "fetch with filtering", "get clean markdown from webpage", "research with content filtering", or needs to fetch web pages with customizable noise removal for LLM processing.
version: 0.1.0
allowed-tools: Read, Write, Bash
---

# fetch4ai Skill

Fetch web content using crawl4ai with customizable filtering strategies. Produces clean, LLM-ready markdown with noise removed.

Can be used as:
1. **Standalone CLI tool** - Simple command-line web fetching with clean output
2. **web-research backend** - Fetching layer for research workflows

## Prerequisites

Ensure crawl4ai is installed:
```bash
pip install -U crawl4ai
crawl4ai-setup  # First-time setup for Playwright
```

## Standalone Quick Use

For simple fetching when you just want clean markdown:

```bash
# Simplest: fetch URL, get markdown output
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://example.com/article" \
  --format markdown

# With timeout control (default: 30s)
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://slow-site.com/page" \
  --format md \
  --timeout 60

# Save directly to file
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://example.com" \
  --format markdown \
  -o content.md
```

### Quiet Mode

Suppress crawl4ai status messages for clean piping:
```bash
# Clean output for piping to other tools
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://example.com" \
  --format md \
  --quiet

# Short form
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://example.com" -q --format md
```

### Shell Alias (Optional)

Add to your `~/.zshrc` or `~/.bashrc`:
```bash
alias fetch4ai='python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py'

# Then use simply:
# fetch4ai --url "https://example.com" --format md -q
```

## Quick Start

### Basic Fetch (Pruning Filter - Default)
```bash
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://example.com/article" \
  --strategy pruning
```

### Query-Focused Fetch (BM25)
```bash
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://example.com/article" \
  --strategy bm25 \
  --query "machine learning applications"
```

### Clean Article Extraction (Tag Exclusion)
```bash
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://example.com/article" \
  --strategy tags \
  --excluded-tags "nav,footer,aside,header"
```

## Filtering Strategies

### Strategy 1: Pruning (Default)

Automatically removes low-quality content by scoring text density, link density, and tag importance.

**When to use:**
- General content extraction from any webpage
- Articles, blog posts, documentation
- Cases without a specific search query

**Parameters:**
- `--threshold` (0.0-1.0, default 0.48): Higher = stricter filtering
- `--min-words` (default 5): Minimum words per content block

**Example:**
```bash
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://en.wikipedia.org/wiki/Artificial_intelligence" \
  --strategy pruning \
  --threshold 0.5
```

### Strategy 2: BM25 (Query-Relevant)

Uses BM25 ranking algorithm to extract only content relevant to your search query.

**When to use:**
- Focused research on specific topics
- Extracting relevant sections from long pages
- Targeted extraction with known search terms

**Parameters:**
- `--query` (required): Search terms for relevance scoring
- `--bm25-threshold` (default 1.2): Minimum relevance score

**Example:**
```bash
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://docs.python.org/3/tutorial/" \
  --strategy bm25 \
  --query "list comprehension syntax"
```

### Strategy 3: Tag Exclusion

Removes specific HTML elements and filters by word count.

**When to use:**
- Clean article extraction
- Removing navigation, footers, sidebars
- Pages with predictable noise elements

**Parameters:**
- `--excluded-tags` (comma-separated): Tags to remove
- `--word-count-threshold` (default 10): Minimum words per block

**Common tag presets:**
- Article: `nav,footer,header,aside`
- Minimal: `nav,footer`
- Aggressive: `nav,footer,header,aside,advertisement,script,style`

**Example:**
```bash
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://example.com/blog/post" \
  --strategy tags \
  --excluded-tags "nav,footer,aside,header,advertisement" \
  --word-count-threshold 15
```

### Strategy 4: Composite (Multi-Pass)

Combine strategies for high-precision extraction: Pruning first, then BM25.

**When to use:**
- Research requiring both noise removal and relevance filtering
- Long pages with scattered relevant content
- Maximum precision extraction

**Example:**
```bash
python ~/.claude/skills/fetch4ai/scripts/fetch4ai.py \
  --url "https://example.com/research-paper" \
  --strategy composite \
  --threshold 0.4 \
  --query "experimental results methodology"
```

## Output Format

The script returns JSON with:

```json
{
  "success": true,
  "url": "https://example.com/article",
  "title": "Page Title",
  "content": "# Clean markdown content...",
  "links": [
    {"text": "Link Text", "href": "https://..."}
  ],
  "stats": {
    "raw_length": 45000,
    "fit_length": 12000,
    "reduction_percent": 73.3
  },
  "strategy": "pruning",
  "metadata": {
    "fetch_time": "2025-01-04T10:30:00",
    "word_count": 2500
  }
}
```

## Advanced Options

### Output Format

```bash
# JSON with full metadata (default)
--format json

# Plain markdown content only (great for piping)
--format markdown
--format md
```

### Timeout Control

```bash
# Default is 30 seconds
--timeout 60  # 60 seconds for slow pages
```

### Include/Exclude Links and Images

```bash
# Include links (default: true)
--include-links

# Include image references
--include-images

# Exclude external links (keep only same-domain)
--exclude-external-links
```

### Session Management (Multi-Page)

For crawling multiple pages with shared browser state:

```bash
# First page
python fetch4ai.py --url "https://example.com/page1" --session-id "my_session"

# Subsequent pages (shares cookies, state)
python fetch4ai.py --url "https://example.com/page2" --session-id "my_session"
```

### Output to File

```bash
python fetch4ai.py --url "https://example.com" --output result.json
```

## Integration with web-research Skill

fetch4ai serves as the fetching layer for the web-research skill:

1. **web-research** spawns research subagents
2. Subagents use **fetch4ai** to get clean content
3. Content is saved to findings files
4. web-research synthesizes all findings

**Usage in research workflow:**
```
# In research subagent prompt:
Use fetch4ai to get content from [URL] with BM25 filtering for "[query]".
Save the fit_markdown to findings_[topic].md.
```

## Error Handling

The script handles common errors:
- Network timeouts (30s default)
- Invalid URLs
- JavaScript-heavy pages (Playwright handles JS)
- Empty content after filtering

Errors return:
```json
{
  "success": false,
  "url": "https://...",
  "error": "Error description",
  "error_type": "timeout|network|parsing|empty_content"
}
```

## Strategy Selection Guide

| Scenario | Strategy | Key Parameters |
|----------|----------|----------------|
| General article | `pruning` | `--threshold 0.48` |
| Specific topic search | `bm25` | `--query "your terms"` |
| Blog/news extraction | `tags` | `--excluded-tags "nav,footer,aside"` |
| Research paper sections | `composite` | `--threshold 0.4 --query "..."` |
| Documentation pages | `pruning` | `--threshold 0.3` (lower for docs) |
| Product listings | `tags` | `--word-count-threshold 20` |

## Reference Documentation

For detailed strategy comparisons and advanced patterns:
- See `references/filtering-strategies.md`
