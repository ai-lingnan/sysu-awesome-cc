#!/usr/bin/env python3
"""
MinerU PDF Converter - Main conversion orchestrator

Convert PDF and other documents to Markdown using MinerU cloud API.
Handles large PDFs (>600 pages) by splitting, converting, and merging.

Usage:
    python mineru_convert.py --input /path/to/file.pdf --token-file /path/to/token.md
    python mineru_convert.py --url https://example.com/file.pdf --token-file /path/to/token.md
"""

import argparse
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Union

import requests

# Optional: For large PDF handling
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


# API Configuration
API_BASE = "https://mineru.net/api/v4"
MAX_PAGES_PER_TASK = 600
SPLIT_CHUNK_SIZE = 500


def load_token(token_file: str) -> str:
    """Load API token from markdown file.

    Token is expected to be in a markdown code block:
    ```
    token_value_here
    ```
    """
    with open(token_file, 'r') as f:
        content = f.read()

    # Extract token from markdown code block
    match = re.search(r'```\n?([^\n`]+)\n?```', content)
    if match:
        return match.group(1).strip()

    # Fallback: return stripped content
    return content.strip()


class MinerUConverter:
    """MinerU API converter client."""

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def upload_file(
        self,
        file_path: Union[str, Path],
        model: str = "vlm",
        extra_formats: Optional[List[str]] = None,
        language: str = "ch",
        enable_formula: bool = True,
        enable_table: bool = True,
        is_ocr: bool = False
    ) -> str:
        """Upload local file and return batch_id.

        Uses the batch upload API to get a presigned URL,
        uploads the file, then returns the batch_id for polling results.

        Note: For local file uploads, tasks are auto-created by the system.
        Use poll_batch_result() to get the conversion results.
        """
        file_path_obj = Path(file_path)
        file_name = file_path_obj.name

        # Step 1: Request upload URL with correct payload format
        # API expects: {"files": [{"name": ...}], "model_version": "vlm", ...}
        payload = {
            "files": [{"name": file_name}],
            "model_version": model,
            "language": language,
            "enable_formula": enable_formula,
            "enable_table": enable_table,
        }

        if extra_formats:
            payload["extra_formats"] = extra_formats

        if is_ocr:
            payload["is_ocr"] = True

        response = requests.post(
            f"{API_BASE}/file-urls/batch",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()

        if result.get("code") != 0:
            raise Exception(f"Failed to get upload URL: {result.get('msg')}")

        batch_id = result["data"]["batch_id"]
        file_urls = result["data"]["file_urls"]

        # file_urls is a list of presigned URLs (strings)
        if not file_urls:
            raise Exception("No upload URLs returned from API")

        upload_url = file_urls[0]

        # Step 2: Upload file content
        # IMPORTANT: Do NOT set Content-Type header - it breaks the OSS signature
        with open(file_path_obj, 'rb') as f:
            file_content = f.read()

        upload_response = requests.put(
            upload_url,
            data=file_content,
            timeout=120
        )
        upload_response.raise_for_status()

        return batch_id

    def poll_batch_result(
        self,
        batch_id: str,
        max_wait: int = 600,
        callback: Optional[Callable[..., Any]] = None
    ) -> Dict[str, Any]:
        """Poll batch result status with exponential backoff.

        For local file uploads, tasks are auto-created by the system.
        This method polls the batch result endpoint to get conversion results.

        Args:
            batch_id: The batch ID from upload_file()
            max_wait: Maximum wait time in seconds
            callback: Optional callback for progress updates

        Returns:
            Result dictionary with file_name, state, and full_zip_url

        Raises:
            TimeoutError: If polling exceeds max_wait
            Exception: If task fails
        """
        start = time.time()
        interval = 2  # Start with 2 seconds
        max_interval = 30

        while time.time() - start < max_wait:
            response = requests.get(
                f"{API_BASE}/extract-results/batch/{batch_id}",
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                raise Exception(f"Failed to get batch status: {result.get('msg')}")

            data = result.get("data", {})
            extract_results = data.get("extract_result", [])

            if extract_results:
                # Get the first result (we upload one file at a time)
                file_result = extract_results[0]
                state = file_result.get("state")

                if callback:
                    callback(state, file_result)

                if state == "done":
                    return file_result
                elif state == "failed":
                    error_msg = file_result.get("err_msg", "Unknown error")
                    raise Exception(f"Batch task failed: {error_msg}")

            # States: pending, running, converting
            time.sleep(interval)
            interval = min(interval * 2, max_interval)

        raise TimeoutError(f"Batch polling timed out after {max_wait} seconds")

    def submit_task(
        self,
        url: str,
        model: str = "vlm",
        language: str = "ch",
        extra_formats: Optional[List[str]] = None,
        enable_formula: bool = True,
        enable_table: bool = True,
        is_ocr: bool = False,
        page_ranges: Optional[str] = None
    ) -> str:
        """Submit conversion task, return task_id."""

        payload = {
            "url": url,
            "model_version": model,
            "language": language,
            "enable_formula": enable_formula,
            "enable_table": enable_table,
        }

        if extra_formats:
            payload["extra_formats"] = extra_formats

        if is_ocr:
            payload["is_ocr"] = True

        if page_ranges:
            payload["page_ranges"] = page_ranges

        response = requests.post(
            f"{API_BASE}/extract/task",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()

        if result.get("code") != 0:
            raise Exception(f"Failed to submit task: {result.get('msg')}")

        return result["data"]["task_id"]

    def poll_task(
        self,
        task_id: str,
        max_wait: int = 600,
        callback: Optional[Callable[..., Any]] = None
    ) -> Dict[str, Any]:
        """Poll task status with exponential backoff.

        Args:
            task_id: The task ID to poll
            max_wait: Maximum wait time in seconds
            callback: Optional callback for progress updates

        Returns:
            Task result dictionary

        Raises:
            TimeoutError: If polling exceeds max_wait
            Exception: If task fails
        """
        start = time.time()
        interval = 2  # Start with 2 seconds
        max_interval = 30

        while time.time() - start < max_wait:
            response = requests.get(
                f"{API_BASE}/extract/task/{task_id}",
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                raise Exception(f"Failed to get task status: {result.get('msg')}")

            data = result.get("data", {})
            state = data.get("state")

            if callback:
                callback(state, data)

            if state == "done":
                return data
            elif state == "failed":
                error_msg = data.get("err_msg", "Unknown error")
                raise Exception(f"Task failed: {error_msg}")

            # States: pending, running, converting
            time.sleep(interval)
            interval = min(interval * 2, max_interval)

        raise TimeoutError(f"Task polling timed out after {max_wait} seconds")

    def download_result(
        self,
        result_url: str,
        output_dir: Union[str, Path],
        extract: bool = True
    ) -> str:
        """Download and extract result ZIP.

        Args:
            result_url: URL to download the result ZIP
            output_dir: Directory to save/extract results
            extract: Whether to extract the ZIP file

        Returns:
            Path to the main .md file (if extracted) or ZIP file
        """
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        # Download ZIP
        response = requests.get(result_url, stream=True)
        response.raise_for_status()

        zip_path = output_dir_path / "result.zip"
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        if not extract:
            return str(zip_path)

        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir_path)

        # Remove ZIP after extraction
        zip_path.unlink()

        # Find the main .md file
        md_files = list(output_dir_path.glob("*.md"))
        if md_files:
            return str(md_files[0])

        # Check subdirectories
        md_files = list(output_dir_path.glob("**/*.md"))
        if md_files:
            return str(md_files[0])

        return str(output_dir_path)

    def get_page_count(self, pdf_path: str) -> int:
        """Get page count of a PDF file using PyMuPDF."""
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF (fitz) is required for page counting. Install with: pip install pymupdf")

        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        return page_count

    def extract_pages(self, pdf_path: str, page_ranges: str, output_path: Optional[str] = None) -> str:
        """Extract specific pages from a PDF file.

        Args:
            pdf_path: Path to the source PDF
            page_ranges: Page ranges string (e.g., "1-10,15,20-25")
            output_path: Optional output path (defaults to temp file)

        Returns:
            Path to the extracted PDF file
        """
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF (fitz) is required for page extraction. Install with: pip install pymupdf")

        # Parse page ranges
        pages_to_extract = self._parse_page_ranges(page_ranges)

        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        # Filter valid page numbers (0-indexed internally, 1-indexed for user)
        valid_pages = [p - 1 for p in pages_to_extract if 1 <= p <= total_pages]

        if not valid_pages:
            doc.close()
            raise ValueError(f"No valid pages in range '{page_ranges}' (document has {total_pages} pages)")

        # Create new document with selected pages
        new_doc = fitz.open()
        for page_num in sorted(valid_pages):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        doc.close()

        # Save to output path
        if output_path is None:
            import tempfile
            fd, output_path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)

        new_doc.save(output_path)
        new_doc.close()

        return output_path

    def _parse_page_ranges(self, page_ranges: str) -> List[int]:
        """Parse page ranges string into list of page numbers.

        Examples:
            "1-5" -> [1, 2, 3, 4, 5]
            "1,3,5-7" -> [1, 3, 5, 6, 7]
            "10-5" -> [5, 6, 7, 8, 9, 10] (handles reversed ranges)
        """
        pages = []
        for part in page_ranges.split(','):
            part = part.strip()
            if '-' in part:
                # Handle range
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())
                if start > end:
                    start, end = end, start
                pages.extend(range(start, end + 1))
            else:
                # Single page
                pages.append(int(part))
        return sorted(set(pages))

    def convert(
        self,
        input_path: Optional[str] = None,
        url: Optional[str] = None,
        output_dir: Optional[str] = None,
        model: str = "vlm",
        language: str = "ch",
        extra_formats: Optional[List[str]] = None,
        enable_formula: bool = True,
        enable_table: bool = True,
        is_ocr: bool = False,
        page_ranges: Optional[str] = None,
        timeout: int = 600,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """Main conversion entry point.

        Args:
            input_path: Local file path (mutually exclusive with url)
            url: Remote file URL (mutually exclusive with input_path)
            output_dir: Output directory (defaults to source directory)
            model: Model version (vlm, pipeline, MinerU-HTML)
            language: Document language
            extra_formats: Additional output formats
            enable_formula: Enable formula recognition
            enable_table: Enable table recognition
            is_ocr: Enable OCR for pipeline model
            page_ranges: Page ranges to convert
            timeout: Max wait time in seconds
            verbose: Print progress updates

        Returns:
            Dictionary with status, output_file, and any warnings
        """
        result = {
            "success": False,
            "output_file": None,
            "warnings": []
        }

        # Validate input
        if not input_path and not url:
            raise ValueError("Either --input or --url must be provided")
        if input_path and url:
            raise ValueError("Cannot provide both --input and --url")

        # Determine output directory
        # When output_dir is not specified, create a subfolder named after the input file
        if output_dir:
            # User specified output directory - use it as-is
            output_dir_path = Path(output_dir)
        elif input_path:
            # Create subfolder named after input file (without extension)
            input_path_obj = Path(input_path)
            subfolder_name = input_path_obj.stem  # filename without extension
            output_dir_path = input_path_obj.parent / subfolder_name
        else:
            # URL input without output_dir - use current directory
            output_dir_path = Path.cwd()

        # Create the output directory early
        output_dir_path.mkdir(parents=True, exist_ok=True)

        # Handle local file - uses batch workflow (auto-created tasks)
        if input_path:
            input_path_resolved = Path(input_path).resolve()

            if not input_path_resolved.exists():
                raise FileNotFoundError(f"Input file not found: {input_path_resolved}")

            # Track if we created a temp file for page extraction
            temp_file_path = None
            file_to_upload = str(input_path_resolved)

            # Handle page_ranges for local PDF files (client-side extraction)
            if page_ranges and input_path_resolved.suffix.lower() == '.pdf' and HAS_PYMUPDF:
                if verbose:
                    print(f"Extracting pages {page_ranges} from PDF...")
                temp_file_path = self.extract_pages(str(input_path_resolved), page_ranges)
                file_to_upload = temp_file_path
                if verbose:
                    extracted_count = self.get_page_count(temp_file_path)
                    print(f"Extracted {extracted_count} pages to temporary file")

            try:
                # Check for large PDF (after page extraction if applicable)
                if Path(file_to_upload).suffix.lower() == '.pdf' and HAS_PYMUPDF:
                    page_count = self.get_page_count(file_to_upload)

                    if page_count > MAX_PAGES_PER_TASK:
                        if verbose:
                            print(f"Large PDF detected ({page_count} pages). Splitting into chunks...")

                        return self._handle_large_pdf(
                            file_to_upload,
                            str(output_dir_path),
                            model=model,
                            language=language,
                            extra_formats=extra_formats,
                            enable_formula=enable_formula,
                            enable_table=enable_table,
                            is_ocr=is_ocr,
                            timeout=timeout,
                            verbose=verbose
                        )

                # Upload file and get batch_id (tasks are auto-created)
                if verbose:
                    print(f"Uploading file: {file_to_upload}")

                batch_id = self.upload_file(
                    file_to_upload,
                    model=model,
                    extra_formats=extra_formats,
                    language=language,
                    enable_formula=enable_formula,
                    enable_table=enable_table,
                    is_ocr=is_ocr
                )

                if verbose:
                    print(f"File uploaded, batch_id: {batch_id}")
                    print(f"Waiting for conversion...")

                # Poll batch result for completion with progress display
                def progress_callback(state, data):
                    if verbose:
                        progress = data.get("extract_progress", {})
                        extracted = progress.get("extracted_pages")
                        total = progress.get("total_pages")
                        if extracted is not None and total:
                            pct = (extracted / total) * 100
                            print(f"Status: {state} ({extracted}/{total} pages, {pct:.1f}%)")
                        else:
                            print(f"Status: {state}")

                batch_result = self.poll_batch_result(
                    batch_id,
                    max_wait=timeout,
                    callback=progress_callback if verbose else None
                )

            finally:
                # Clean up temp file if we created one
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except Exception:
                        pass

            # Download result
            result_url = batch_result.get("full_zip_url")
            if not result_url:
                raise Exception("No result URL in batch response")

            if verbose:
                print(f"Downloading result...")

            output_file = self.download_result(result_url, str(output_dir_path))

            result["success"] = True
            result["output_file"] = output_file
            result["batch_id"] = batch_id

            return result

        # Handle URL input - uses task workflow (manual task submission)
        if verbose:
            print(f"Submitting conversion task for URL...")

        # url is guaranteed to be str here since we checked input_path above
        task_id = self.submit_task(
            url=url,  # type: ignore
            model=model,
            language=language,
            extra_formats=extra_formats,
            enable_formula=enable_formula,
            enable_table=enable_table,
            is_ocr=is_ocr,
            page_ranges=page_ranges
        )

        if verbose:
            print(f"Task submitted: {task_id}")

        # Poll for completion with progress display
        def progress_callback(state, data):
            if verbose:
                progress = data.get("extract_progress", {})
                extracted = progress.get("extracted_pages")
                total = progress.get("total_pages")
                if extracted is not None and total:
                    pct = (extracted / total) * 100
                    print(f"Status: {state} ({extracted}/{total} pages, {pct:.1f}%)")
                else:
                    print(f"Status: {state}")

        task_result = self.poll_task(
            task_id,
            max_wait=timeout,
            callback=progress_callback if verbose else None
        )

        # Download result
        result_url = task_result.get("full_zip_url")
        if not result_url:
            raise Exception("No result URL in task response")

        if verbose:
            print(f"Downloading result...")

        output_file = self.download_result(result_url, str(output_dir_path))

        result["success"] = True
        result["output_file"] = output_file
        result["task_id"] = task_id

        return result

    def _handle_large_pdf(
        self,
        pdf_path: str,
        output_dir: str,
        model: str,
        language: str,
        extra_formats: Optional[List[str]],
        enable_formula: bool,
        enable_table: bool,
        is_ocr: bool,
        timeout: int,
        verbose: bool
    ) -> Dict[str, Any]:
        """Handle PDFs over 600 pages by splitting and merging.

        Note: output_dir is already resolved by convert() - it will be a subfolder
        named after the input file when --output-dir is not specified.
        """

        # Import splitter and merger
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))

        from pdf_splitter import split_pdf
        from merge_markdown import merge_markdown_files

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Split PDF
        if verbose:
            print(f"Splitting PDF into {SPLIT_CHUNK_SIZE}-page chunks...")

        chunks = split_pdf(pdf_path, SPLIT_CHUNK_SIZE)

        if verbose:
            print(f"Created {len(chunks)} chunks")

        # Convert each chunk
        output_files = []
        warnings = []

        for i, chunk_path in enumerate(chunks):
            if verbose:
                print(f"Converting chunk {i+1}/{len(chunks)}...")

            try:
                # Create chunk-specific output directory
                chunk_output_dir = Path(output_dir) / f"chunk_{i+1}"
                chunk_output_dir.mkdir(parents=True, exist_ok=True)

                # Upload chunk and get batch_id with all parameters
                batch_id = self.upload_file(
                    chunk_path,
                    model=model,
                    extra_formats=extra_formats,
                    language=language,
                    enable_formula=enable_formula,
                    enable_table=enable_table,
                    is_ocr=is_ocr
                )

                if verbose:
                    print(f"  Chunk {i+1} uploaded, batch_id: {batch_id}")

                # Poll batch result for completion
                batch_result = self.poll_batch_result(batch_id, max_wait=timeout)

                # Download result
                result_url = batch_result.get("full_zip_url")
                if result_url:
                    output_file = self.download_result(result_url, str(chunk_output_dir))
                    output_files.append(output_file)
                else:
                    warnings.append(f"Chunk {i+1}: No result URL")

            except Exception as e:
                warnings.append(f"Chunk {i+1} failed: {str(e)}")

            finally:
                # Clean up chunk file
                try:
                    os.remove(chunk_path)
                except Exception:
                    pass

        # Merge outputs
        if output_files:
            if verbose:
                print("Merging output files...")

            # Get original filename without extension
            original_name = Path(pdf_path).stem
            final_output = Path(output_dir) / f"{original_name}.md"

            merge_markdown_files(output_files, str(final_output))

            # Clean up chunk directories
            for chunk_dir in Path(output_dir).glob("chunk_*"):
                if chunk_dir.is_dir():
                    import shutil
                    shutil.rmtree(chunk_dir)

            return {
                "success": True,
                "output_file": str(final_output),
                "warnings": warnings,
                "chunks_processed": len(output_files)
            }
        else:
            return {
                "success": False,
                "output_file": None,
                "warnings": warnings,
                "error": "All chunks failed"
            }


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF to Markdown using MinerU API"
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input", "-i",
        help="Local file path to convert"
    )
    input_group.add_argument(
        "--url", "-u",
        help="Remote file URL to convert"
    )

    # Required options
    parser.add_argument(
        "--token-file", "-t",
        required=True,
        help="Path to token file"
    )

    # Model options
    parser.add_argument(
        "--model", "-m",
        default="vlm",
        choices=["vlm", "pipeline", "MinerU-HTML"],
        help="Model version (default: vlm)"
    )
    parser.add_argument(
        "--language", "-l",
        default="ch",
        help="Document language (default: ch)"
    )

    # Output options
    parser.add_argument(
        "--output-dir", "-o",
        help="Output directory (default: same as source)"
    )
    parser.add_argument(
        "--extra-formats",
        nargs="+",
        choices=["latex", "docx", "html"],
        help="Additional output formats"
    )

    # Recognition options
    parser.add_argument(
        "--enable-formula",
        type=lambda x: x.lower() == 'true',
        default=True,
        help="Enable formula recognition (default: true)"
    )
    parser.add_argument(
        "--enable-table",
        type=lambda x: x.lower() == 'true',
        default=True,
        help="Enable table recognition (default: true)"
    )
    parser.add_argument(
        "--is-ocr",
        action="store_true",
        help="Enable OCR (for pipeline model)"
    )
    parser.add_argument(
        "--page-ranges",
        help="Page ranges to convert (e.g., '1-100,150-200')"
    )

    # Processing options
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Max wait time in seconds (default: 600)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print progress updates"
    )

    args = parser.parse_args()

    try:
        # Load token
        token = load_token(args.token_file)

        # Create converter
        converter = MinerUConverter(token)

        # Run conversion
        result = converter.convert(
            input_path=args.input,
            url=args.url,
            output_dir=args.output_dir,
            model=args.model,
            language=args.language,
            extra_formats=args.extra_formats,
            enable_formula=args.enable_formula,
            enable_table=args.enable_table,
            is_ocr=args.is_ocr,
            page_ranges=args.page_ranges,
            timeout=args.timeout,
            verbose=args.verbose
        )

        # Output result as JSON
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result["success"]:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
