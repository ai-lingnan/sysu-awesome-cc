# Filtering Strategies Reference

Detailed comparison and advanced usage patterns for fetch4ai filtering strategies.

## Strategy Comparison Matrix

| Strategy | Best For | Pros | Cons | LLM Dependency |
|----------|----------|------|------|----------------|
| **Pruning** | General extraction | Fast, no query needed, automatic | May miss relevant low-density content | None |
| **BM25** | Topic-focused research | Precise relevance, great for search | Requires query, may be too strict | None |
| **Tags** | Article extraction | Predictable, explicit control | Requires knowing page structure | None |
| **Composite** | Research papers | Maximum precision | Slower (2 passes), needs query | None |

## Strategy 1: Pruning Filter

### How It Works

PruningContentFilter scores each HTML node based on:

1. **Text Density**: Ratio of text to HTML markup
2. **Link Density**: Ratio of link text to total text (high = likely navigation)
3. **Tag Importance**: Semantic weight (article > div > aside)
4. **Word Count**: Blocks below threshold are discarded

Nodes scoring below the threshold are removed.

### Threshold Tuning Guide

| Threshold | Effect | Use Case |
|-----------|--------|----------|
| 0.3 | Permissive | Documentation, tutorials (keep more content) |
| 0.48 | Balanced | Articles, blog posts (default) |
| 0.6 | Strict | News sites with heavy ads |
| 0.8 | Very strict | Extract only main content |

### Example: Documentation Site

```bash
# Lower threshold for docs (they have less dense content)
python fetch4ai.py \
  --url "https://docs.python.org/3/library/asyncio.html" \
  --strategy pruning \
  --threshold 0.3 \
  --min-words 3
```

### Example: Ad-Heavy News Site

```bash
# Higher threshold to remove ads
python fetch4ai.py \
  --url "https://example-news.com/article" \
  --strategy pruning \
  --threshold 0.6
```

## Strategy 2: BM25 Filter

### How It Works

BM25 (Best Matching 25) is a probabilistic ranking algorithm that:

1. Tokenizes content into chunks
2. Calculates term frequency (TF) for query terms
3. Applies inverse document frequency (IDF) weighting
4. Scores chunks by relevance to query
5. Returns chunks above threshold

### Query Writing Tips

**Good queries:**
- Specific terms: `"async await python syntax"`
- Multiple related terms: `"machine learning neural network"`
- Key concepts: `"API authentication JWT tokens"`

**Poor queries:**
- Too broad: `"code"` (matches everything)
- Too narrow: `"asyncio.create_task line 47"` (too specific)

### Threshold Tuning

| BM25 Threshold | Effect |
|----------------|--------|
| 0.3 | Very permissive - many matches |
| 0.5 | Permissive - more matches |
| 0.8 | Balanced (default) |
| 1.2 | Strict - focused results |
| 2.0+ | Very strict - may return empty |

**Note:** BM25 can be aggressive on some pages. If you get empty results, try lowering the threshold or using pruning strategy instead.

### Example: Research Topic

```bash
# Find sections about specific methodology
python fetch4ai.py \
  --url "https://arxiv.org/abs/2301.00001" \
  --strategy bm25 \
  --query "experimental results accuracy metrics" \
  --bm25-threshold 1.5
```

## Strategy 3: Tag Exclusion

### How It Works

Simple but effective:
1. Remove specified HTML tags entirely
2. Filter remaining blocks by word count
3. Convert to markdown

### Common Tag Presets

**Minimal (safe):**
```bash
--excluded-tags "nav,footer"
```

**Standard (recommended):**
```bash
--excluded-tags "nav,footer,header,aside"
```

**Aggressive (for cluttered sites):**
```bash
--excluded-tags "nav,footer,header,aside,advertisement,script,style,noscript,iframe"
```

**E-commerce:**
```bash
--excluded-tags "nav,footer,header,aside,advertisement,related-products,reviews"
```

### Word Count Threshold

| Threshold | Effect |
|-----------|--------|
| 5 | Keep most blocks |
| 10 | Default - removes tiny snippets |
| 20 | Removes short paragraphs |
| 50 | Only substantial paragraphs |

### Example: Blog Post

```bash
python fetch4ai.py \
  --url "https://blog.example.com/post" \
  --strategy tags \
  --excluded-tags "nav,footer,header,aside,advertisement,social-share" \
  --word-count-threshold 15
```

## Strategy 4: Composite (Two-Pass)

### How It Works

1. **Pass 1 (Pruning)**: Remove noise based on content density
2. **Pass 2 (BM25)**: Extract query-relevant chunks from cleaned content

This maximizes precision for research use cases.

### When to Use

- Long documents with scattered relevant content
- Research papers or technical documentation
- When single-pass strategies miss important content or include too much noise

### Configuration Tips

- Use lower pruning threshold (0.3-0.4) in first pass to preserve more content
- Use higher BM25 threshold (1.5-2.0) in second pass for precision

### Example: Academic Paper

```bash
python fetch4ai.py \
  --url "https://arxiv.org/html/2401.00001" \
  --strategy composite \
  --threshold 0.35 \
  --query "methodology experimental design results" \
  --bm25-threshold 1.5
```

## Multi-Page Crawling

### Session Management

Use `--session-id` to share browser state across pages:

```bash
# Login page
python fetch4ai.py \
  --url "https://example.com/login" \
  --session-id "research_session"

# Protected content (uses same session/cookies)
python fetch4ai.py \
  --url "https://example.com/protected/article" \
  --session-id "research_session" \
  --strategy bm25 \
  --query "relevant content"
```

### Research Workflow

1. Fetch seed URL with pruning
2. Extract links from result
3. Fetch linked pages with BM25 for specific query
4. Aggregate content

```bash
# Step 1: Get main page and links
python fetch4ai.py --url "https://example.com" --strategy pruning -o main.json

# Step 2: Fetch linked articles (parse links from main.json)
python fetch4ai.py --url "https://example.com/article1" --strategy bm25 --query "topic" -o article1.json
python fetch4ai.py --url "https://example.com/article2" --strategy bm25 --query "topic" -o article2.json
```

## Troubleshooting

### Empty Content

**Cause**: Threshold too high or wrong tags excluded

**Solutions:**
- Lower threshold: `--threshold 0.3`
- Reduce excluded tags
- Try different strategy

### Missing Relevant Content

**Cause**: BM25 threshold too high or query too narrow

**Solutions:**
- Lower BM25 threshold: `--bm25-threshold 0.8`
- Broaden query terms
- Use composite with lower pruning threshold

### Too Much Noise

**Cause**: Threshold too low or not enough tags excluded

**Solutions:**
- Increase threshold: `--threshold 0.6`
- Add more excluded tags
- Use BM25 for focused extraction

### JavaScript Content Not Loading

**Cause**: Page requires more time to render

**Solutions:**
- crawl4ai uses Playwright which handles JS
- Content should load automatically
- If issues persist, page may have anti-bot measures
