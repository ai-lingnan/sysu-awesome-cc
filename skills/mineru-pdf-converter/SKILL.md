---
name: mineru-pdf-converter
description: This skill should be used when the user asks to "convert PDF to markdown", "use MinerU to convert [file]", "extract text from PDF", "PDF转Markdown", "转换PDF [路径]", "MinerU转换 [file]", "/mineru [file path]", or needs high-quality document conversion with formula and table recognition.
version: 1.1.0
allowed-tools: Bash, Read, Write
---

# MinerU PDF Converter

Convert PDF and other documents to high-quality Markdown using MinerU cloud API. Handles large PDFs (>600 pages) automatically by splitting, converting, and merging.

## Capabilities

- Convert PDF, images, and other documents to Markdown/LaTeX
- Preserve formulas, tables, and complex layouts
- Auto-upload local files via MinerU batch API
- Auto-split large PDFs (>600 pages) and merge results
- Support additional output formats: LaTeX, DOCX, HTML

## Requirements

**Python packages:**
```bash
pip install requests pymupdf
```

**API Token:**
Token stored at: `~/.claude/skills/mineru-pdf-converter/references/mineru-token.md`

## Quick Start

### Basic Conversion

```bash
python ~/.claude/skills/mineru-pdf-converter/scripts/mineru_convert.py \
  --input "/path/to/document.pdf" \
  --token-file "~/.claude/skills/mineru-pdf-converter/references/mineru-token.md"
```

### Convert from URL

```bash
python ~/.claude/skills/mineru-pdf-converter/scripts/mineru_convert.py \
  --url "https://example.com/paper.pdf" \
  --token-file "~/.claude/skills/mineru-pdf-converter/references/mineru-token.md"
```

### Verbose Mode with Progress

```bash
python ~/.claude/skills/mineru-pdf-converter/scripts/mineru_convert.py \
  --input "/path/to/document.pdf" \
  --token-file "~/.claude/skills/mineru-pdf-converter/references/mineru-token.md" \
  --verbose
```

Output shows progress percentage during conversion:
```
Uploading file: /path/to/document.pdf
File uploaded, batch_id: abc123
Waiting for conversion...
Status: running (25/100 pages, 25.0%)
Status: running (50/100 pages, 50.0%)
Status: done
Downloading result...
```

### Additional Formats

```bash
# Include LaTeX output
python ~/.claude/skills/mineru-pdf-converter/scripts/mineru_convert.py \
  --input "/path/to/document.pdf" \
  --token-file "~/.claude/skills/mineru-pdf-converter/references/mineru-token.md" \
  --extra-formats "latex"
```

## Workflow

When user requests PDF conversion:

1. **Identify input type**
   - Local file path: Use batch upload API to get temporary URL
   - URL: Submit directly to conversion API

2. **Check file size (for PDFs)**
   - If >600 pages: Split into 500-page chunks using PyMuPDF
   - Process each chunk separately
   - Merge final Markdown output

3. **Execute conversion**
   ```bash
   python ~/.claude/skills/mineru-pdf-converter/scripts/mineru_convert.py \
     --input "[path]" \
     --token-file "~/.claude/skills/mineru-pdf-converter/references/mineru-token.md"
   ```

4. **Report result**
   - Confirm output path (subfolder named after input file by default)
   - Note any warnings or partial failures
   - Provide path to main .md file

## Parameters Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--input` | - | Local file path (mutually exclusive with --url) |
| `--url` | - | Remote file URL (mutually exclusive with --input) |
| `--token-file` | - | Path to token file (required) |
| `--model` | vlm | Model: pipeline, vlm, MinerU-HTML |
| `--language` | ch | Document language |
| `--extra-formats` | [] | Additional formats: latex, docx, html |
| `--output-dir` | (source dir/filename) | Override output directory (skips subfolder creation) |
| `--enable-formula` | true | Enable formula recognition |
| `--enable-table` | true | Enable table recognition |
| `--page-ranges` | - | Page ranges to convert (e.g., "1-100,150-200") - see note below |
| `--timeout` | 600 | Max wait time in seconds |

## Page Ranges

The `--page-ranges` parameter allows you to convert only specific pages:

```bash
# Convert pages 1-50 and 100-150
python ~/.claude/skills/mineru-pdf-converter/scripts/mineru_convert.py \
  --input "/path/to/document.pdf" \
  --page-ranges "1-50,100-150" \
  --token-file "~/.claude/skills/mineru-pdf-converter/references/mineru-token.md"
```

**How it works:**
- **Local files (`--input`)**: Pages are extracted client-side using PyMuPDF before upload
- **URL input (`--url`)**: Page ranges sent to MinerU API server-side

This means page ranges now work for both local files and URLs.

## Large PDF Handling

PDFs over 600 pages are automatically:
1. Split into chunks of max 500 pages using PyMuPDF
2. Each chunk converted separately via the API
3. Output Markdown files merged in order with page markers
4. Temporary chunk files cleaned up

To handle large PDFs, ensure PyMuPDF is installed:
```bash
pip install pymupdf
```

## Model Selection

| Model | Best For | Notes |
|-------|----------|-------|
| vlm (default) | Complex layouts, formulas, tables | Higher accuracy, handles scanned documents |
| pipeline | Simple text documents | Faster processing, lower resource usage |
| MinerU-HTML | HTML output needed | Specialized for HTML output format |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Auth failed (401) | Invalid or expired token | Update token in mineru.md |
| Task timeout | Large file or slow server | Increase --timeout; retry later |
| Conversion failed | Unsupported format or corrupted file | Try pipeline model as fallback |
| Upload failed (413) | File >200MB | Split file manually first |
| Rate limit (429) | Exceeded 2000 pages/day quota | Wait until next day |

## Output Structure

The conversion produces a ZIP file that is extracted to a **subfolder named after the input file**. This prevents naming conflicts when converting multiple PDFs in the same directory.

**Default behavior (no `--output-dir` specified):**

For input `/path/to/paper.pdf`, output is saved to `/path/to/paper/`:
```
/path/to/paper/
├── full.md               # Main Markdown file
├── images/               # Extracted images
│   ├── image_1.png
│   └── image_2.png
└── paper.json            # Structured content (optional)
```

**With `--output-dir` specified:**

When `--output-dir /custom/path` is provided, files are extracted directly to that directory (no subfolder created):
```
/custom/path/
├── full.md
├── images/
│   └── ...
└── paper.json
```

## API Quota

- High priority: 2000 pages/day
- Low priority: Additional capacity (slower processing)
- Check remaining quota in the API response

## Supporting Files

- **`scripts/mineru_convert.py`** - Main conversion orchestrator
- **`scripts/pdf_splitter.py`** - PDF splitting utility (PyMuPDF)
- **`scripts/merge_markdown.py`** - Output merger for chunked conversions
- **`references/api-reference.md`** - Full MinerU API documentation

## Troubleshooting

### Token Expired
The JWT token has an expiration date. If authentication fails:
1. Log in to mineru.net
2. Get a new API token
3. Update `~/.claude/skills/mineru-pdf-converter/references/mineru-token.md`

### Conversion Hangs
For very large or complex documents:
1. Increase timeout: `--timeout 1200`
2. Use page ranges to convert in sections: `--page-ranges "1-100"`
3. Try the pipeline model: `--model pipeline`

### Missing Formulas or Tables
Ensure recognition is enabled (default):
- `--enable-formula true`
- `--enable-table true`

For detailed API reference, see `references/api-reference.md`.
