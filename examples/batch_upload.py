#!/usr/bin/env python3
"""
Batch Upload Example
Processes multiple PDF and Markdown files and uploads them to Webflow.
"""

import sys
from pathlib import Path

# Add parent directory to path to import webflow_uploader
sys.path.insert(0, str(Path(__file__).parent.parent))

from webflow_uploader import WebflowUploader


def batch_upload_directory(directory, api_token, collection_id, publish=False):
    """
    Upload all PDF and Markdown files from a directory.

    Args:
        directory: Path to directory containing files
        api_token: Webflow API token
        collection_id: Webflow collection ID
        publish: Whether to publish immediately
    """
    uploader = WebflowUploader(api_token, collection_id)

    # Find all supported files
    directory = Path(directory)
    files = list(directory.glob("*.pdf")) + list(directory.glob("*.md"))

    print(f"Found {len(files)} files to upload")
    print("-" * 50)

    results = {
        "success": [],
        "failed": []
    }

    # Process each file
    for file_path in files:
        try:
            print(f"\nProcessing: {file_path.name}")
            result = uploader.process_and_upload(
                str(file_path),
                published=publish
            )
            results["success"].append(file_path.name)
            print(f"✓ Success!")

        except Exception as e:
            print(f"✗ Failed: {e}")
            results["failed"].append((file_path.name, str(e)))

    # Print summary
    print("\n" + "=" * 50)
    print(f"SUMMARY")
    print("=" * 50)
    print(f"Total files: {len(files)}")
    print(f"Successful: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")

    if results["failed"]:
        print("\nFailed files:")
        for filename, error in results["failed"]:
            print(f"  - {filename}: {error}")


if __name__ == "__main__":
    # Configuration
    API_TOKEN = "your-webflow-api-token"
    COLLECTION_ID = "your-collection-id"
    ARTICLES_DIR = "./articles"  # Directory containing your PDF/MD files
    AUTO_PUBLISH = False  # Set to True to publish immediately

    # Run batch upload
    batch_upload_directory(
        directory=ARTICLES_DIR,
        api_token=API_TOKEN,
        collection_id=COLLECTION_ID,
        publish=AUTO_PUBLISH
    )
