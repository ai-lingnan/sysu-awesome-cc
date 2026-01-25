#!/usr/bin/env python3
"""
Markdown Merger Utility

Merge multiple Markdown files from chunked PDF conversion into a single file.
Handles page markers, image references, and proper formatting.

Usage:
    from merge_markdown import merge_markdown_files
    merge_markdown_files(["/path/to/chunk1.md", "/path/to/chunk2.md"], "/path/to/output.md")
"""

import re
import shutil
from pathlib import Path
from typing import List, Optional, Union


def extract_images_from_markdown(md_content: str) -> List[str]:
    """Extract image references from Markdown content.

    Args:
        md_content: Markdown content string

    Returns:
        List of image paths/URLs found in the content
    """
    # Match both ![alt](path) and <img src="path"> formats
    patterns = [
        r'!\[([^\]]*)\]\(([^)]+)\)',  # ![alt](path)
        r'<img[^>]+src=["\']([^"\']+)["\']',  # <img src="path">
    ]

    images = []
    for pattern in patterns:
        matches = re.findall(pattern, md_content)
        if matches:
            # Handle tuple matches from first pattern
            if isinstance(matches[0], tuple):
                images.extend([m[1] for m in matches])
            else:
                images.extend(matches)

    return images


def update_image_paths(
    md_content: str,
    old_base: str,
    new_base: str,
    chunk_num: int
) -> str:
    """Update image paths in Markdown content.

    Args:
        md_content: Markdown content string
        old_base: Original base path for images
        new_base: New base path for images
        chunk_num: Chunk number for unique naming

    Returns:
        Updated Markdown content
    """
    def replace_path(match):
        alt_text = match.group(1)
        old_path = match.group(2)

        # Skip URLs
        if old_path.startswith(('http://', 'https://')):
            return match.group(0)

        # Get just the filename
        filename = Path(old_path).name

        # Add chunk prefix to avoid conflicts
        new_filename = f"chunk{chunk_num}_{filename}"
        new_path = f"{new_base}/{new_filename}"

        return f"![{alt_text}]({new_path})"

    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    return re.sub(pattern, replace_path, md_content)


def merge_markdown_files(
    input_files: List[Union[str, Path]],
    output_path: Union[str, Path],
    add_page_markers: bool = True,
    copy_images: bool = True,
    images_subdir: str = "images"
) -> str:
    """Merge multiple Markdown files into one.

    Args:
        input_files: List of paths to Markdown files to merge
        output_path: Path for the merged output file
        add_page_markers: Add chunk/page markers between sections
        copy_images: Copy referenced images to output directory
        images_subdir: Subdirectory name for images

    Returns:
        Path to the merged Markdown file
    """
    output_path_obj = Path(output_path)
    output_dir = output_path_obj.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create images directory if copying images
    if copy_images:
        images_dir = output_dir / images_subdir
        images_dir.mkdir(parents=True, exist_ok=True)

    merged_content = []

    for i, input_file in enumerate(input_files):
        input_path = Path(input_file)

        if not input_path.exists():
            continue

        # Read content
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add page marker
        if add_page_markers and i > 0:
            merged_content.append(f"\n\n---\n\n<!-- Chunk {i + 1} -->\n\n")

        # Handle images
        if copy_images:
            # Find and copy images
            images = extract_images_from_markdown(content)
            input_dir = input_path.parent

            for img_ref in images:
                # Skip URLs
                if img_ref.startswith(('http://', 'https://')):
                    continue

                # Find source image
                img_path = input_dir / img_ref
                if not img_path.exists():
                    # Try looking in parent directories
                    for parent in [input_dir.parent, input_dir.parent.parent]:
                        candidate = parent / Path(img_ref).name
                        if candidate.exists():
                            img_path = candidate
                            break

                if img_path.exists():
                    # Copy with unique name
                    new_name = f"chunk{i + 1}_{img_path.name}"
                    dest_path = images_dir / new_name
                    shutil.copy2(img_path, dest_path)

            # Update image references in content
            content = update_image_paths(content, str(input_dir), images_subdir, i + 1)

        merged_content.append(content.strip())

    # Write merged file
    final_content = "\n\n".join(merged_content)

    with open(output_path_obj, 'w', encoding='utf-8') as f:
        f.write(final_content)

    return str(output_path_obj)


def merge_with_metadata(
    input_files: List[str],
    output_path: str,
    source_file: Optional[str] = None
) -> str:
    """Merge Markdown files with metadata header.

    Args:
        input_files: List of paths to Markdown files to merge
        output_path: Path for the merged output file
        source_file: Original source file name for metadata

    Returns:
        Path to the merged Markdown file
    """
    from datetime import datetime

    # Create metadata header
    metadata = [
        "---",
        f"created: {datetime.now().strftime('%Y-%m-%d')}",
        f"source: {source_file or 'unknown'}",
        f"chunks: {len(input_files)}",
        "converter: MinerU",
        "---",
        ""
    ]

    # Merge files
    result_path = merge_markdown_files(input_files, output_path)

    # Prepend metadata
    with open(result_path, 'r', encoding='utf-8') as f:
        content = f.read()

    with open(result_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(metadata) + '\n' + content)

    return result_path


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Merge Markdown files")
    parser.add_argument(
        "input_files",
        nargs="+",
        help="Markdown files to merge"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output file path"
    )
    parser.add_argument(
        "--no-page-markers",
        action="store_true",
        help="Don't add page markers between chunks"
    )
    parser.add_argument(
        "--no-copy-images",
        action="store_true",
        help="Don't copy images to output directory"
    )
    parser.add_argument(
        "--with-metadata",
        action="store_true",
        help="Add metadata header to output"
    )
    parser.add_argument(
        "--source",
        help="Source file name for metadata"
    )

    args = parser.parse_args()

    if args.with_metadata:
        result = merge_with_metadata(
            args.input_files,
            args.output,
            source_file=args.source
        )
    else:
        result = merge_markdown_files(
            args.input_files,
            args.output,
            add_page_markers=not args.no_page_markers,
            copy_images=not args.no_copy_images
        )

    output = {
        "success": True,
        "output_file": result,
        "input_count": len(args.input_files)
    }
    print(json.dumps(output, indent=2))
