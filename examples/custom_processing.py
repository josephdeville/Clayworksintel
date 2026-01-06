#!/usr/bin/env python3
"""
Custom Processing Example
Demonstrates how to extend the WebflowUploader with custom processing logic.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from webflow_uploader import WebflowUploader


class CustomWebflowUploader(WebflowUploader):
    """Extended uploader with custom processing logic."""

    def process_file(self, file_path):
        """Override to add custom preprocessing."""
        # Get base content
        content = super().process_file(file_path)

        # Add custom processing
        # Example: Auto-tag based on keywords
        content["tags"] = self.auto_tag(content["body"])

        # Example: Generate SEO-friendly excerpt
        if not content.get("excerpt"):
            content["excerpt"] = self.generate_excerpt(content["body"])

        # Example: Add reading time
        content["reading_time"] = self.calculate_reading_time(content["body"])

        return content

    def auto_tag(self, text):
        """Automatically generate tags based on content."""
        keywords = {
            "python": ["python", "py", "django", "flask"],
            "javascript": ["javascript", "js", "node", "react"],
            "automation": ["automate", "automation", "script"],
            "ai": ["ai", "machine learning", "ml", "neural"]
        }

        text_lower = text.lower()
        tags = []

        for tag, keywords_list in keywords.items():
            if any(keyword in text_lower for keyword in keywords_list):
                tags.append(tag)

        return tags

    def generate_excerpt(self, text, max_length=160):
        """Generate SEO-friendly excerpt."""
        # Remove markdown formatting
        import re
        plain_text = re.sub(r'[#*_`\[\]()]', '', text)
        plain_text = ' '.join(plain_text.split())

        # Get first sentence or max_length characters
        sentences = plain_text.split('.')
        excerpt = sentences[0] if sentences else plain_text

        if len(excerpt) > max_length:
            excerpt = excerpt[:max_length].rsplit(' ', 1)[0] + '...'

        return excerpt.strip()

    def calculate_reading_time(self, text):
        """Calculate estimated reading time in minutes."""
        words = len(text.split())
        reading_speed = 200  # Average words per minute
        minutes = max(1, round(words / reading_speed))
        return f"{minutes} min read"

    def format_for_webflow(self, content, published=False, featured_image_url=None):
        """Override to add custom fields."""
        # Get base formatting
        webflow_item = super().format_for_webflow(content, published, featured_image_url)

        # Add custom field
        if content.get("reading_time"):
            webflow_item["fields"]["reading-time"] = content["reading_time"]

        return webflow_item


def main():
    """Example usage of custom uploader."""
    # Initialize custom uploader
    uploader = CustomWebflowUploader(
        api_token="your-api-token",
        collection_id="your-collection-id"
    )

    # Process file with custom logic
    result = uploader.process_and_upload(
        "sample_article.md",
        published=False,
        dry_run=True  # Test without uploading
    )

    # Display results
    print("Title:", result["content"]["title"])
    print("Auto-generated tags:", result["content"]["tags"])
    print("Excerpt:", result["content"]["excerpt"])
    print("Reading time:", result["content"]["reading_time"])


if __name__ == "__main__":
    main()
