#!/usr/bin/env python3
"""
Webflow PDF/Markdown Uploader
Processes PDF and Markdown files to extract content and metadata
for uploading as articles/blogs to Webflow CMS.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import requests
import markdown
from bs4 import BeautifulSoup

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


class WebflowUploader:
    """Handle PDF and Markdown file uploads to Webflow CMS."""

    def __init__(self, api_token: str, collection_id: str):
        """
        Initialize the Webflow uploader.

        Args:
            api_token: Webflow API token
            collection_id: Webflow collection ID for blog/articles
        """
        self.api_token = api_token
        self.collection_id = collection_id
        self.base_url = "https://api.webflow.com"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "accept-version": "1.0.0",
            "Content-Type": "application/json"
        }

    def extract_pdf_content(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract content from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary containing title, content, metadata
        """
        content = {
            "title": "",
            "body": "",
            "metadata": {},
            "images": [],
            "links": []
        }

        if pdfplumber:
            # Use pdfplumber (better for complex PDFs)
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata
                if pdf.metadata:
                    content["metadata"] = {
                        "author": pdf.metadata.get("Author", ""),
                        "creator": pdf.metadata.get("Creator", ""),
                        "producer": pdf.metadata.get("Producer", ""),
                        "subject": pdf.metadata.get("Subject", ""),
                        "created_date": pdf.metadata.get("CreationDate", "")
                    }
                    # Use title from metadata if available
                    if pdf.metadata.get("Title"):
                        content["title"] = pdf.metadata.get("Title")

                # Extract text from all pages
                full_text = []
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        full_text.append(text)

                        # Extract first non-empty line as title if not set
                        if not content["title"] and page_num == 1:
                            lines = [line.strip() for line in text.split('\n') if line.strip()]
                            if lines:
                                content["title"] = lines[0]

                content["body"] = "\n\n".join(full_text)

        elif PyPDF2:
            # Fallback to PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract metadata
                if pdf_reader.metadata:
                    content["metadata"] = {
                        "author": pdf_reader.metadata.get("/Author", ""),
                        "creator": pdf_reader.metadata.get("/Creator", ""),
                        "producer": pdf_reader.metadata.get("/Producer", ""),
                        "subject": pdf_reader.metadata.get("/Subject", ""),
                        "title": pdf_reader.metadata.get("/Title", "")
                    }
                    if content["metadata"]["title"]:
                        content["title"] = content["metadata"]["title"]

                # Extract text from all pages
                full_text = []
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        full_text.append(text)

                        # Extract first line as title if not set
                        if not content["title"] and page_num == 1:
                            lines = [line.strip() for line in text.split('\n') if line.strip()]
                            if lines:
                                content["title"] = lines[0]

                content["body"] = "\n\n".join(full_text)
        else:
            raise ImportError("Neither pdfplumber nor PyPDF2 is installed. Install one to process PDFs.")

        # If still no title, use filename
        if not content["title"]:
            content["title"] = Path(pdf_path).stem.replace('-', ' ').replace('_', ' ').title()

        return content

    def extract_markdown_content(self, md_path: str) -> Dict[str, any]:
        """
        Extract content from Markdown file.

        Args:
            md_path: Path to Markdown file

        Returns:
            Dictionary containing title, content, metadata
        """
        with open(md_path, 'r', encoding='utf-8') as file:
            raw_content = file.read()

        content = {
            "title": "",
            "body": "",
            "body_html": "",
            "metadata": {},
            "tags": [],
            "category": "",
            "author": "",
            "excerpt": ""
        }

        # Extract YAML frontmatter if present
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        frontmatter_match = re.match(frontmatter_pattern, raw_content, re.DOTALL)

        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            # Parse YAML-like frontmatter
            for line in frontmatter_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip().strip('"').strip("'")

                    if key == 'title':
                        content["title"] = value
                    elif key == 'author':
                        content["author"] = value
                    elif key == 'category':
                        content["category"] = value
                    elif key == 'tags':
                        # Handle tags as comma-separated or list
                        if value.startswith('['):
                            content["tags"] = [t.strip().strip('"').strip("'")
                                             for t in value.strip('[]').split(',')]
                        else:
                            content["tags"] = [t.strip() for t in value.split(',')]
                    elif key == 'excerpt' or key == 'description':
                        content["excerpt"] = value
                    else:
                        content["metadata"][key] = value

            # Remove frontmatter from content
            raw_content = raw_content[frontmatter_match.end():]

        # Convert markdown to HTML
        content["body"] = raw_content.strip()
        content["body_html"] = markdown.markdown(
            raw_content,
            extensions=['extra', 'codehilite', 'toc', 'tables']
        )

        # Extract title from first H1 if not in frontmatter
        if not content["title"]:
            h1_match = re.search(r'^#\s+(.+)$', raw_content, re.MULTILINE)
            if h1_match:
                content["title"] = h1_match.group(1).strip()
            else:
                # Use filename as fallback
                content["title"] = Path(md_path).stem.replace('-', ' ').replace('_', ' ').title()

        # Generate excerpt if not provided (first 160 chars of content)
        if not content["excerpt"]:
            # Remove markdown formatting for excerpt
            plain_text = re.sub(r'[#*_`\[\]()]', '', raw_content)
            plain_text = ' '.join(plain_text.split())
            content["excerpt"] = plain_text[:160] + '...' if len(plain_text) > 160 else plain_text

        return content

    def process_file(self, file_path: str) -> Dict[str, any]:
        """
        Process a file (PDF or Markdown) and extract content.

        Args:
            file_path: Path to the file

        Returns:
            Extracted content dictionary
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() == '.pdf':
            return self.extract_pdf_content(str(file_path))
        elif file_path.suffix.lower() in ['.md', '.markdown']:
            return self.extract_markdown_content(str(file_path))
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def format_for_webflow(self, content: Dict[str, any],
                          published: bool = False,
                          featured_image_url: Optional[str] = None) -> Dict[str, any]:
        """
        Format extracted content for Webflow CMS API.

        Args:
            content: Extracted content dictionary
            published: Whether to publish immediately
            featured_image_url: URL of featured image (optional)

        Returns:
            Webflow-formatted item dictionary
        """
        # Create slug from title
        slug = re.sub(r'[^a-z0-9]+', '-', content["title"].lower()).strip('-')

        # Prepare Webflow item
        webflow_item = {
            "fields": {
                "name": content["title"],  # Required: item name
                "slug": slug,  # Required: URL slug
                "_archived": False,
                "_draft": not published
            }
        }

        # Add body content (field name may vary - commonly 'post-body' or 'body')
        if "body_html" in content and content["body_html"]:
            webflow_item["fields"]["post-body"] = content["body_html"]
        else:
            # Convert plain text to HTML paragraphs
            paragraphs = content.get("body", "").split('\n\n')
            html_body = ''.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])
            webflow_item["fields"]["post-body"] = html_body

        # Add optional fields
        if content.get("excerpt"):
            webflow_item["fields"]["post-summary"] = content["excerpt"]

        if content.get("author"):
            webflow_item["fields"]["author-name"] = content["author"]

        if content.get("category"):
            webflow_item["fields"]["category"] = content["category"]

        if featured_image_url:
            webflow_item["fields"]["main-image"] = {
                "url": featured_image_url
            }

        # Add tags if supported
        if content.get("tags"):
            webflow_item["fields"]["tags"] = content["tags"]

        # Add metadata as custom fields
        if content.get("metadata"):
            for key, value in content["metadata"].items():
                # Convert metadata keys to kebab-case
                field_key = re.sub(r'[^a-z0-9]+', '-', key.lower()).strip('-')
                webflow_item["fields"][field_key] = value

        return webflow_item

    def upload_to_webflow(self, webflow_item: Dict[str, any]) -> Dict[str, any]:
        """
        Upload item to Webflow CMS.

        Args:
            webflow_item: Formatted Webflow item

        Returns:
            Response from Webflow API
        """
        url = f"{self.base_url}/collections/{self.collection_id}/items"

        response = requests.post(
            url,
            headers=self.headers,
            json=webflow_item
        )

        response.raise_for_status()
        return response.json()

    def update_webflow_item(self, item_id: str, webflow_item: Dict[str, any]) -> Dict[str, any]:
        """
        Update existing Webflow CMS item.

        Args:
            item_id: Webflow item ID
            webflow_item: Formatted Webflow item

        Returns:
            Response from Webflow API
        """
        url = f"{self.base_url}/collections/{self.collection_id}/items/{item_id}"

        response = requests.patch(
            url,
            headers=self.headers,
            json=webflow_item
        )

        response.raise_for_status()
        return response.json()

    def process_and_upload(self, file_path: str,
                          published: bool = False,
                          featured_image_url: Optional[str] = None,
                          dry_run: bool = False) -> Dict[str, any]:
        """
        Complete workflow: process file and upload to Webflow.

        Args:
            file_path: Path to PDF or Markdown file
            published: Whether to publish immediately
            featured_image_url: URL of featured image
            dry_run: If True, only process but don't upload

        Returns:
            Result dictionary with content and upload response
        """
        # Extract content
        print(f"Processing {file_path}...")
        content = self.process_file(file_path)
        print(f"✓ Extracted content: '{content['title']}'")

        # Format for Webflow
        webflow_item = self.format_for_webflow(
            content,
            published=published,
            featured_image_url=featured_image_url
        )
        print(f"✓ Formatted for Webflow")

        result = {
            "file_path": file_path,
            "content": content,
            "webflow_item": webflow_item,
            "upload_response": None
        }

        # Upload to Webflow
        if not dry_run:
            print(f"Uploading to Webflow...")
            upload_response = self.upload_to_webflow(webflow_item)
            result["upload_response"] = upload_response
            print(f"✓ Successfully uploaded! Item ID: {upload_response.get('_id', 'N/A')}")
        else:
            print(f"✓ Dry run - skipping upload")

        return result


def main():
    """Command-line interface for the uploader."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Upload PDF or Markdown files to Webflow CMS'
    )
    parser.add_argument('files', nargs='+', help='PDF or Markdown files to upload')
    parser.add_argument('--api-token', required=True, help='Webflow API token')
    parser.add_argument('--collection-id', required=True, help='Webflow collection ID')
    parser.add_argument('--publish', action='store_true', help='Publish immediately')
    parser.add_argument('--featured-image', help='URL of featured image')
    parser.add_argument('--dry-run', action='store_true', help='Process without uploading')
    parser.add_argument('--output', help='Save extracted content to JSON file')

    args = parser.parse_args()

    # Initialize uploader
    uploader = WebflowUploader(args.api_token, args.collection_id)

    # Process each file
    results = []
    for file_path in args.files:
        try:
            result = uploader.process_and_upload(
                file_path,
                published=args.publish,
                featured_image_url=args.featured_image,
                dry_run=args.dry_run
            )
            results.append(result)
            print()
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            print()

    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to {args.output}")

    print(f"Processed {len(results)}/{len(args.files)} files successfully")


if __name__ == "__main__":
    main()
