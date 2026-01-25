#!/usr/bin/env python3
"""
PDF Splitter Utility

Split large PDF files into smaller chunks for processing.
Uses PyMuPDF (fitz) for efficient PDF manipulation.

Usage:
    from pdf_splitter import split_pdf
    chunks = split_pdf("/path/to/large.pdf", chunk_size=500)
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional, Union

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF is required. Install with: pip install pymupdf")


def get_page_count(pdf_path: str) -> int:
    """Get the number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Number of pages
    """
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count


def split_pdf(
    pdf_path: Union[str, Path],
    chunk_size: int = 500,
    output_dir: Optional[Union[str, Path]] = None,
    prefix: Optional[str] = None
) -> List[str]:
    """Split a PDF file into chunks of specified size.

    Args:
        pdf_path: Path to the source PDF file
        chunk_size: Maximum pages per chunk (default: 500)
        output_dir: Directory to save chunks (default: temp directory)
        prefix: Prefix for chunk filenames (default: source filename)

    Returns:
        List of paths to the chunk files
    """
    pdf_path_obj = Path(pdf_path)

    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path_obj}")

    # Set up output directory
    if output_dir:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
    else:
        output_dir_path = Path(tempfile.mkdtemp(prefix="pdf_chunks_"))

    # Set up prefix
    if not prefix:
        prefix = pdf_path_obj.stem

    # Open source PDF
    doc = fitz.open(str(pdf_path_obj))
    total_pages = len(doc)

    if total_pages <= chunk_size:
        # No splitting needed
        doc.close()
        return [str(pdf_path_obj)]

    # Calculate chunks
    chunks = []
    chunk_num = 0

    for start_page in range(0, total_pages, chunk_size):
        end_page = min(start_page + chunk_size, total_pages)
        chunk_num += 1

        # Create chunk filename
        chunk_filename = f"{prefix}_chunk_{chunk_num:03d}.pdf"
        chunk_path = output_dir_path / chunk_filename

        # Create new PDF for this chunk
        chunk_doc = fitz.open()
        chunk_doc.insert_pdf(doc, from_page=start_page, to_page=end_page - 1)
        chunk_doc.save(str(chunk_path))
        chunk_doc.close()

        chunks.append(str(chunk_path))

    doc.close()

    return chunks


def merge_pdfs(
    pdf_paths: List[Union[str, Path]],
    output_path: Union[str, Path]
) -> str:
    """Merge multiple PDF files into one.

    Args:
        pdf_paths: List of paths to PDF files to merge
        output_path: Path for the merged output file

    Returns:
        Path to the merged PDF file
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    merged_doc = fitz.open()

    for pdf_path in pdf_paths:
        pdf_path_obj = Path(pdf_path)
        if pdf_path_obj.exists():
            doc = fitz.open(str(pdf_path_obj))
            merged_doc.insert_pdf(doc)
            doc.close()

    merged_doc.save(str(output_path_obj))
    merged_doc.close()

    return str(output_path_obj)


def get_pdf_info(pdf_path: str) -> dict:
    """Get information about a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary with PDF metadata
    """
    doc = fitz.open(pdf_path)

    info = {
        "path": pdf_path,
        "page_count": len(doc),
        "metadata": doc.metadata,
        "is_encrypted": doc.is_encrypted,
        "needs_pass": doc.needs_pass,
    }

    # Get file size
    file_size = os.path.getsize(pdf_path)
    info["file_size_mb"] = round(file_size / (1024 * 1024), 2)

    doc.close()

    return info


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Split PDF into chunks")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument(
        "--chunk-size", "-c",
        type=int,
        default=500,
        help="Maximum pages per chunk (default: 500)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        help="Output directory for chunks"
    )
    parser.add_argument(
        "--info-only",
        action="store_true",
        help="Only show PDF info, don't split"
    )

    args = parser.parse_args()

    if args.info_only:
        info = get_pdf_info(args.pdf_path)
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        chunks = split_pdf(
            args.pdf_path,
            chunk_size=args.chunk_size,
            output_dir=args.output_dir
        )

        result = {
            "source": args.pdf_path,
            "chunk_count": len(chunks),
            "chunks": chunks
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
