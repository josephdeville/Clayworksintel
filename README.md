# Clayworksintel - Webflow PDF/Markdown Uploader

A Python tool to process PDF and Markdown files and upload them as articles/blogs to Webflow CMS.

## Features

- **PDF Processing**: Extract content, metadata, title, and text from PDF files
- **Markdown Processing**: Parse Markdown files with YAML frontmatter support
- **Webflow Integration**: Upload directly to Webflow CMS via API
- **Flexible Configuration**: Support for custom field mappings and settings
- **Metadata Extraction**: Automatically extract author, tags, categories, and more
- **Draft/Publish Control**: Choose to save as draft or publish immediately
- **Dry Run Mode**: Test extraction without uploading

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Clayworksintel
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Webflow credentials:
```bash
cp config.example.json config.json
# Edit config.json with your Webflow API token and collection ID
```

## Configuration

### Getting Webflow Credentials

1. **API Token**:
   - Go to Webflow Dashboard → Project Settings → Integrations → API Access
   - Generate a new API token
   - Copy the token to `config.json`

2. **Collection ID**:
   - In Webflow, go to your CMS Collections
   - Use the Webflow API or browser developer tools to find your collection ID
   - Typically visible in the URL or API responses

### Configuration File

Edit `config.json`:

```json
{
  "webflow": {
    "api_token": "your-api-token-here",
    "collection_id": "your-collection-id-here"
  },
  "upload_settings": {
    "auto_publish": false,
    "default_author": "Your Name"
  }
}
```

## Usage

### Command Line Interface

**Basic upload (as draft):**
```bash
python webflow_uploader.py article.pdf \
  --api-token YOUR_TOKEN \
  --collection-id YOUR_COLLECTION_ID
```

**Upload and publish immediately:**
```bash
python webflow_uploader.py article.md \
  --api-token YOUR_TOKEN \
  --collection-id YOUR_COLLECTION_ID \
  --publish
```

**Upload multiple files:**
```bash
python webflow_uploader.py article1.pdf article2.md article3.md \
  --api-token YOUR_TOKEN \
  --collection-id YOUR_COLLECTION_ID
```

**Dry run (test without uploading):**
```bash
python webflow_uploader.py article.pdf \
  --api-token YOUR_TOKEN \
  --collection-id YOUR_COLLECTION_ID \
  --dry-run
```

**With featured image:**
```bash
python webflow_uploader.py article.md \
  --api-token YOUR_TOKEN \
  --collection-id YOUR_COLLECTION_ID \
  --featured-image https://example.com/image.jpg
```

**Save extracted content to JSON:**
```bash
python webflow_uploader.py article.pdf \
  --api-token YOUR_TOKEN \
  --collection-id YOUR_COLLECTION_ID \
  --dry-run \
  --output extracted_content.json
```

### Python API Usage

```python
from webflow_uploader import WebflowUploader

# Initialize uploader
uploader = WebflowUploader(
    api_token="your-api-token",
    collection_id="your-collection-id"
)

# Process and upload a file
result = uploader.process_and_upload(
    file_path="article.pdf",
    published=False,
    featured_image_url="https://example.com/image.jpg"
)

print(f"Uploaded: {result['content']['title']}")
print(f"Item ID: {result['upload_response']['_id']}")
```

### Markdown File Format

For best results, use YAML frontmatter in your Markdown files:

```markdown
---
title: My Article Title
author: John Doe
category: Technology
tags: [python, webflow, automation]
excerpt: A brief description of the article
date: 2024-01-06
---

# My Article Title

Your article content here...

## Section 1

Content...
```

**Supported Frontmatter Fields:**
- `title`: Article title
- `author`: Author name
- `category`: Article category
- `tags`: List of tags (array or comma-separated)
- `excerpt`/`description`: Short summary
- `date`: Publication date
- Any custom fields you've added to your Webflow collection

### PDF File Processing

The uploader automatically extracts:
- **Title**: From PDF metadata or first heading
- **Content**: All text from all pages
- **Metadata**: Author, creator, subject, dates
- **Structure**: Maintains paragraph breaks

## Webflow Field Mapping

The uploader maps content to common Webflow field names:

| Content | Webflow Field |
|---------|---------------|
| Title | `name` (required) |
| URL Slug | `slug` (auto-generated) |
| Body HTML | `post-body` |
| Excerpt | `post-summary` |
| Author | `author-name` |
| Category | `category` |
| Featured Image | `main-image` |
| Tags | `tags` |

**Note**: Field names may vary based on your Webflow collection setup. You may need to adjust the field mappings in `webflow_uploader.py` (see `format_for_webflow` method).

## Advanced Usage

### Custom Field Mappings

To customize field mappings, edit the `format_for_webflow` method in `webflow_uploader.py`:

```python
def format_for_webflow(self, content, published=False):
    webflow_item = {
        "fields": {
            "name": content["title"],
            "slug": self.generate_slug(content["title"]),
            "your-custom-field": content.get("custom_data", "")
        }
    }
    return webflow_item
```

### Batch Processing Script

Create a script to process multiple files:

```python
from pathlib import Path
from webflow_uploader import WebflowUploader

uploader = WebflowUploader("your-token", "your-collection-id")

# Process all PDFs in a directory
pdf_dir = Path("./articles")
for pdf_file in pdf_dir.glob("*.pdf"):
    result = uploader.process_and_upload(str(pdf_file))
    print(f"✓ Uploaded: {result['content']['title']}")
```

### Update Existing Items

To update an existing Webflow item:

```python
# Extract and format content
content = uploader.process_file("article.pdf")
webflow_item = uploader.format_for_webflow(content, published=True)

# Update existing item
response = uploader.update_webflow_item(
    item_id="existing-item-id",
    webflow_item=webflow_item
)
```

## Troubleshooting

### PDF Extraction Issues

If PDF text extraction isn't working well:
1. Ensure PDFs are text-based (not scanned images)
2. Try converting scanned PDFs with OCR first
3. Use `pdfplumber` for complex layouts (already included)

### Webflow API Errors

**401 Unauthorized**: Check your API token is correct and has proper permissions

**404 Not Found**: Verify your collection ID is correct

**400 Bad Request**: Check field names match your Webflow collection schema

### Field Mapping Issues

If uploads fail due to field mismatches:
1. Check your Webflow collection field names
2. Update field mappings in `format_for_webflow` method
3. Use `--dry-run` and `--output` to inspect the generated data

## Requirements

- Python 3.7+
- Internet connection for Webflow API
- Valid Webflow API token with CMS write permissions

## Dependencies

See `requirements.txt` for full list:
- PyPDF2: PDF text extraction
- pdfplumber: Advanced PDF processing
- markdown: Markdown to HTML conversion
- beautifulsoup4: HTML parsing
- requests: HTTP client for Webflow API
- PyYAML: YAML frontmatter parsing

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check the Webflow API documentation: https://developers.webflow.com/
2. Review your collection's field schema in Webflow
3. Use `--dry-run` mode to debug content extraction

## Contributing

Contributions welcome! Please submit issues or pull requests.

## Examples

See the `examples/` directory for:
- Sample Markdown files with frontmatter
- Sample batch processing scripts
- Custom field mapping examples
