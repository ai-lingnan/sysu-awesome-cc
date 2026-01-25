# MinerU API Reference

Complete API documentation for MinerU cloud document conversion service.

## Base URL

```
https://mineru.net/api/v4
```

## Authentication

All requests require a Bearer token in the Authorization header:

```
Authorization: Bearer {token}
Content-Type: application/json
```

Token location: `~/.claude/skills/mineru-pdf-converter/references/mineru-token.md`

## Endpoints

### 1. File Upload (Batch)

Upload local files to get temporary URLs for conversion. Tasks are automatically created after upload.

**Endpoint:** `POST /file-urls/batch`

**Request:**
```json
{
  "files": [
    {"name": "document.pdf"},
    {"name": "paper.pdf"}
  ],
  "model_version": "vlm",
  "language": "ch",
  "extra_formats": ["latex"],
  "enable_formula": true,
  "enable_table": true,
  "is_ocr": false
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| files | object[] | Yes | - | Array of file objects with "name" field |
| model_version | string | No | vlm | Model: "vlm", "pipeline", "MinerU-HTML" |
| language | string | No | ch | Document language |
| extra_formats | string[] | No | [] | Additional: "latex", "docx", "html" |
| enable_formula | bool | No | true | Enable formula recognition |
| enable_table | bool | No | true | Enable table recognition |
| is_ocr | bool | No | false | Enable OCR (pipeline model only) |

**Response:**
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "batch_id": "abc123",
    "file_urls": [
      "https://storage.example.com/upload/document.pdf?signature=..."
    ]
  }
}
```

**Upload Process:**
1. Request upload URL from this endpoint with conversion parameters
2. PUT file content to the returned URL (NO Content-Type header)
3. Poll `/extract-results/batch/{batch_id}` for results (tasks auto-created)

**Upload File Content:**
```
PUT {upload_url}

[binary file content]
```

**IMPORTANT:** Do NOT set `Content-Type` header when uploading - it breaks the OSS signature verification.

**Note:** `page_ranges` parameter is NOT supported for batch upload. Use URL-based task submission if you need page ranges.

### 2. Create Conversion Task

Submit a single file for conversion.

**Endpoint:** `POST /extract/task`

**Request:**
```json
{
  "url": "https://example.com/document.pdf",
  "model_version": "vlm",
  "language": "ch",
  "extra_formats": ["latex"],
  "enable_formula": true,
  "enable_table": true,
  "is_ocr": false,
  "page_ranges": "1-100,150-200"
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | Yes | - | File URL (public or uploaded) |
| model_version | string | No | vlm | Model: "vlm", "pipeline", "MinerU-HTML" |
| language | string | No | ch | Document language |
| extra_formats | string[] | No | [] | Additional: "latex", "docx", "html" |
| enable_formula | bool | No | true | Enable formula recognition |
| enable_table | bool | No | true | Enable table recognition |
| is_ocr | bool | No | false | Enable OCR (pipeline model only) |
| page_ranges | string | No | - | Page ranges (e.g., "1-100,150-200") |

**Response:**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "task_id": "task_abc123"
  }
}
```

### 3. Get Task Result

Poll for task completion and get results.

**Endpoint:** `GET /extract/task/{task_id}`

**Response (pending/running):**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "task_id": "task_abc123",
    "state": "running",
    "progress": 50
  }
}
```

**Response (done):**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "task_id": "task_abc123",
    "state": "done",
    "full_zip_url": "https://storage.example.com/results/task_abc123.zip",
    "md_url": "https://storage.example.com/results/task_abc123.md",
    "page_count": 50,
    "used_pages": 50
  }
}
```

**Response (failed):**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "task_id": "task_abc123",
    "state": "failed",
    "err_msg": "Unsupported file format"
  }
}
```

**Task States:**

| State | Description |
|-------|-------------|
| pending | Task queued, waiting to start |
| running | Conversion in progress |
| converting | Post-processing formats |
| done | Completed successfully |
| failed | Conversion failed |

### 4. Batch Task Creation

Create multiple conversion tasks at once.

**Endpoint:** `POST /extract/task/batch`

**Request:**
```json
{
  "files": [
    {
      "url": "https://example.com/doc1.pdf",
      "model_version": "vlm"
    },
    {
      "url": "https://example.com/doc2.pdf",
      "model_version": "pipeline"
    }
  ]
}
```

**Response:**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "batch_id": "batch_xyz789"
  }
}
```

### 5. Get Batch Results

Get results for a batch of tasks (used after batch file upload).

**Endpoint:** `GET /extract-results/batch/{batch_id}`

**Response (running):**
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "batch_id": "batch_xyz789",
    "extract_result": [
      {
        "file_name": "document.pdf",
        "state": "running",
        "extract_progress": {
          "extracted_pages": 25,
          "total_pages": 100,
          "start_time": "2026-01-24 12:00:00"
        }
      }
    ]
  }
}
```

**Response (done):**
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "batch_id": "batch_xyz789",
    "extract_result": [
      {
        "file_name": "document.pdf",
        "state": "done",
        "full_zip_url": "https://cdn-mineru.openxlab.org.cn/pdf/abc123.zip"
      }
    ]
  }
}
```

**Note:** The response uses `extract_result` (singular), not `extract_results` (plural).

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| 0 | 200 | Success |
| 401 | 401 | Authentication failed - invalid or expired token |
| 403 | 403 | Forbidden - insufficient permissions |
| 413 | 413 | File too large (>200MB) |
| 429 | 429 | Rate limit exceeded |
| 500 | 500 | Internal server error |

## Constraints

| Constraint | Value |
|------------|-------|
| Max file size | 200 MB |
| Max pages per task | 600 |
| Daily high-priority quota | 2000 pages |
| Recommended chunk size | 500 pages |
| URL timeout for external files | 60 seconds |

## Model Comparison

### VLM (Vision Language Model)

- Best for: Complex layouts, scanned documents, formulas
- Accuracy: Highest
- Speed: Slower
- Features: OCR built-in, handles images and tables well

### Pipeline

- Best for: Simple text documents, digital PDFs
- Accuracy: Good for clean documents
- Speed: Faster
- Features: Optional OCR, lighter processing

### MinerU-HTML

- Best for: HTML output requirement
- Accuracy: Similar to VLM
- Speed: Moderate
- Features: Produces structured HTML output

## Polling Strategy

Recommended exponential backoff:

```
Initial interval: 2 seconds
Max interval: 30 seconds
Formula: min(2^attempts * 2, 30)
Max timeout: 600 seconds (10 minutes)
```

**Sequence:**
1. Wait 2s
2. Wait 4s
3. Wait 8s
4. Wait 16s
5. Wait 30s (capped)
6. Continue at 30s intervals

## Output Format

The result ZIP contains:

```
result.zip/
├── document.md           # Main Markdown output
├── document.json         # Structured content (optional)
├── images/               # Extracted images
│   ├── page_1_img_1.png
│   └── page_2_img_1.png
└── extra/                # Additional formats (if requested)
    ├── document.tex      # LaTeX (if extra_formats includes "latex")
    └── document.docx     # Word (if extra_formats includes "docx")
```

## Troubleshooting

### Authentication Errors

**Symptom:** HTTP 401 or code -1 with auth message

**Solutions:**
1. Verify token is not expired (JWT has expiration)
2. Ensure token is correctly extracted from markdown file
3. Regenerate token from mineru.net dashboard

### Task Timeout

**Symptom:** Polling exceeds max_wait without completion

**Solutions:**
1. Increase timeout for large documents
2. Use page_ranges to convert in sections
3. Split large PDFs before submitting
4. Try during off-peak hours

### Conversion Failures

**Symptom:** Task state = "failed"

**Common causes:**
- Unsupported file format
- Corrupted PDF
- Password-protected document
- File too large (>200MB)
- Too many pages (>600)

**Solutions:**
1. Verify file opens in PDF reader
2. Check file size (<200MB)
3. Remove password protection
4. Split into smaller chunks

### Upload Failures

**Symptom:** PUT to upload URL fails with 403 SignatureDoesNotMatch

**Solutions:**
1. Do NOT set Content-Type header (breaks OSS signature)
2. Verify file is readable
3. Check file size (<200MB)
4. Retry with fresh upload URL (they expire after 24 hours)

### Missing Formula/Table Recognition

**Symptom:** Formulas rendered as images or tables not detected

**Solutions:**
1. Ensure enable_formula=true
2. Ensure enable_table=true
3. Use VLM model (best for complex content)
4. Try increasing image quality in source PDF

## Rate Limiting

### Daily Quotas

- High priority: 2000 pages/day
- Quota resets at midnight (UTC+8)

### Handling Rate Limits

When receiving 429 error:
1. Check remaining quota in response headers
2. Wait until quota reset
3. Consider using lower priority for non-urgent tasks

## Best Practices

1. **Pre-check file size** before upload
2. **Split large PDFs** (>600 pages) into 500-page chunks
3. **Use exponential backoff** for polling
4. **Handle all task states** including pending and converting
5. **Clean up temporary files** after processing
6. **Monitor daily quota** to avoid unexpected failures
7. **Cache results** when converting the same document multiple times
8. **Use page_ranges** for partial document conversion
9. **Log task IDs** for debugging and tracking
10. **Implement retry logic** for transient failures
