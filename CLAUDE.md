# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with this Japanese cinema web scraping project.

## Project Overview

A specialized web scraping toolkit for extracting movie schedule information from Japanese cinema websites. The project focuses on extracting structured data including movie titles, screening schedules, cast information, and event details, then outputting to CSV files with optional Google Sheets integration.

**Key Features:**
- Multi-format HTML parsing for various cinema websites
- Batch processing capabilities with CLI tools
- Japanese text support with proper encoding
- Google Sheets integration for data management
- Comprehensive analysis tools for HTML structure compatibility

## Technology Stack

### Core Dependencies
- **Python**: >=3.11 (managed with uv)
- **BeautifulSoup4**: HTML parsing and scraping
- **Pandas**: Data manipulation and CSV export
- **Requests**: HTTP client for web scraping
- **Jupyter**: Interactive development environment
- **gspread + oauth2client**: Google Sheets API integration

### Development Environment Setup
```bash
# Install all dependencies
uv sync

# Verify installation
uv run python --version
uv run python -c "import pandas, bs4; print('Dependencies OK')"
```

## Core Scripts and Usage

### 1. Single File Processing
```bash
# Process one HTML file
uv run python scrape_single_html.py "html/cinema_schedule.html"
```

### 2. Batch Processing
```bash
# Process all HTML files in directory
uv run python scrape_all_html.py

# Advanced batch processing with options
uv run python batch_scraper.py html/*.html --combine --verbose
uv run python batch_scraper.py html/shimotakaido.html html/eurospace.html -c -v
```

### 3. HTML Structure Analysis
```bash
# Analyze all HTML files for compatibility
uv run python html_analyzer.py all

# Detailed analysis of specific file
uv run python html_analyzer.py "html/cinema.html" detailed
```

### 4. Development Environment
```bash
# Start Jupyter notebook for interactive development
uv run jupyter notebook

# Launch specific notebook
uv run jupyter notebook notebook/test.ipynb
```

## Project Architecture

```
scraping_theatre/
├── scrape_single_html.py     # Single file processor
├── scrape_all_html.py        # Batch processor (simple)
├── batch_scraper.py          # Advanced batch processor with CLI
├── html_analyzer.py          # HTML structure analysis tool
├── hello.py                  # Entry point script
├── notebook/
│   └── test.ipynb           # Main development notebook
├── html/                    # Sample HTML files for testing
├── data/                    # Output CSV files
├── doc/
│   ├── manual.md           # Comprehensive setup guide
│   └── scraping_scripts.md # Japanese usage documentation
├── pyproject.toml          # Project configuration
└── uv.lock                 # Dependency lock file
```

## Data Extraction Schema

The scraper extracts structured movie data with the following fields:

| Field | Japanese | Description |
|-------|----------|-------------|
| タイトル | Title | Movie title |
| 特集名 | Special Feature | Special screening series name |
| 制作年/国/時間 | Year/Country/Duration | Production details |
| 監督/出演 | Director/Cast | Director and cast information |
| 概要 | Synopsis | Movie synopsis/description |
| 上映スケジュール | Screening Schedule | Show times and dates |
| 料金 | Pricing | Ticket pricing information |
| 受賞歴 | Awards | Awards and recognition |
| イベント情報 | Event Information | Special events and Q&A sessions |
| シネマ名 | Cinema Name | Source cinema name (auto-added) |
| ファイル名 | Source Filename | Source HTML filename (batch mode) |

## HTML Parsing Strategy

### Target HTML Structure
The scrapers are optimized for the following HTML patterns:
```html
<div class="box">
    <span class="eiga-title">Movie Title</span>
    <span class="title-s">Special Feature Title</span>
    <p class="stuff">Production info and cast</p>
    <p class="note">Synopsis</p>
    <p class="day">Screening schedule</p>
    <p class="price">Pricing</p>
    <p class="syo">Awards</p>
    <p class="p3">Event information</p>
</div>
```

### Compatibility Status
- ✅ **下高井戸シネマ (Shimotakaido Cinema)**: Full compatibility - 65+ movies extracted
- ⚠️ **ポレポレ東中野**: Partial compatibility - different structure
- ⚠️ **ユーロスペース**: Requires custom parsing
- ⚠️ **早稲田松竹**: Non-standard HTML structure
- ❌ **Other cinemas**: Require custom scrapers

### Special Features Support
- **Regular movies**: Standard `span.eiga-title` extraction
- **Special screenings**: `span.title-s` with nested `details` elements
- **Retrospective series**: Handles grouped movie collections
- **Error handling**: Robust parsing with fallback mechanisms

## Core Functions Reference

### Notebook Functions (notebook/test.ipynb)
```python
# Main scraping function (URL-based)
scrape_movie_info(url: str) -> pandas.DataFrame

# HTML file processing
process_html_file(file_path: str) -> pandas.DataFrame

# Individual movie data extraction
process_movie_box(box, is_special=False, special_title=None) -> dict

# Text cleaning utility
clean_text(text: str) -> str

# Google Sheets upload
upload_to_sheets(df, credentials_path, spreadsheet_name) -> str
```

### Script Functions
All standalone scripts share the same core functions:
- `scrape_html_file(file_path)`: Process local HTML file
- `process_movie_box()`: Extract movie data from HTML elements
- `clean_text()`: Normalize Japanese text and whitespace

## Google Sheets Integration

### Setup Requirements
1. **Google Cloud Console**: Enable Sheets API and Drive API
2. **Service Account**: Create and download JSON credentials
3. **Dependencies**: Install `gspread` and `oauth2client`

### Usage Example
```python
# Upload scraped data to Google Sheets
credentials_path = "path/to/service-account-key.json"
spreadsheet_name = "Cinema Movie Database"
url = upload_to_sheets(df, credentials_path, spreadsheet_name)
print(f"Data uploaded: {url}")
```

### Features
- **Auto-creation**: Creates spreadsheet if it doesn't exist
- **Date-stamped sheets**: New worksheet for each scraping session
- **Column auto-resize**: Optimizes display formatting
- **Error handling**: Graceful failure with detailed error messages

## Development Workflow

### 1. HTML Analysis Phase
```bash
# Analyze new cinema HTML structure
uv run python html_analyzer.py "html/new_cinema.html" detailed

# Check compatibility across all files
uv run python html_analyzer.py all
```

### 2. Script Development
```bash
# Interactive development in Jupyter
uv run jupyter notebook notebook/test.ipynb

# Test single file processing
uv run python scrape_single_html.py "html/test_file.html"
```

### 3. Batch Processing
```bash
# Process all compatible files
uv run python scrape_all_html.py

# Advanced batch with custom options
uv run python batch_scraper.py html/*.html --combine --verbose
```

### 4. Data Validation
- Check CSV output in `data/` directory
- Verify Japanese text encoding (UTF-8)
- Validate extracted movie counts
- Review sample data output

## Testing and Quality Assurance

### Sample Data
- **HTML files**: Representative samples in `html/` directory
- **Expected output**: Known good CSV files in `data/` directory
- **Edge cases**: Special features, multi-day screenings, award information

### Validation Checklist
- [ ] Japanese text properly encoded (UTF-8)
- [ ] Movie titles extracted correctly
- [ ] Screening schedules formatted properly
- [ ] Special feature grouping works
- [ ] Error handling doesn't crash on malformed HTML
- [ ] CSV output opens correctly in Excel/Sheets

## Common Issues and Solutions

### HTML Parsing Issues
**Problem**: New cinema websites with different HTML structure
**Solution**: Use `html_analyzer.py` to identify structure, then create custom parser

### Japanese Text Encoding
**Problem**: Garbled Japanese characters in output
**Solution**: Ensure all file operations use `encoding="utf-8"`

### Google Sheets Authentication
**Problem**: Authentication errors with Google Sheets API
**Solution**: Verify service account JSON file path and API permissions

### Performance with Large Files
**Problem**: Memory issues with large HTML files
**Solution**: Use batch processing with `batch_scraper.py` instead of processing all at once

## Documentation References

- **`doc/manual.md`**: Complete setup and configuration guide
- **`doc/scraping_scripts.md`**: Japanese documentation with usage examples
- **Source code**: Inline documentation in all Python files
- **Jupyter notebook**: Interactive examples and development notes