# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a theatre/cinema web scraping project focused on extracting movie schedule information from Japanese cinema websites. The project scrapes movie information including titles, schedules, directors, cast, and event details, then saves the data to CSV files for management. It also includes functionality to upload data to Google Sheets.

## Development Environment

### Python Environment
- Uses uv for dependency management
- Python >=3.11 required
- Main dependencies: beautifulsoup4, pandas, jupyter, ipykernel

### Common Commands
```bash
# Install dependencies
uv sync

# Run HTML scraping scripts
uv run python scrape_single_html.py "html/filename.html"
uv run python scrape_all_html.py
uv run python batch_scraper.py html/*.html -c -v
uv run python html_analyzer.py all

# Start Jupyter for development
uv run jupyter notebook
```

## Project Structure

### Core Components
- `hello.py`: Entry point script
- `notebook/test.ipynb`: Main development notebook containing scraping logic
- `doc/manual.md`: Comprehensive manual with setup instructions and code documentation
- `doc/scraping_scripts.md`: Japanese documentation for HTML scraping scripts
- `data/`: Output directory for scraped data (CSV files)
- `html/`: Sample HTML files from various cinema websites

### HTML Scraping Scripts
- `scrape_single_html.py`: Process a single HTML file
- `scrape_all_html.py`: Process all HTML files in html directory
- `batch_scraper.py`: Advanced batch processing with CLI options
- `html_analyzer.py`: Analyze HTML structure and compatibility

### Key Functions (in notebook/test.ipynb)
- `scrape_movie_info(url)`: Main scraping function that processes cinema websites
- `process_movie_box(box, is_special=False, special_title=None)`: Processes individual movie information blocks
- `clean_text(text)`: Text cleaning utility
- `upload_to_sheets()`: Google Sheets integration (requires credentials)

## Data Structure

The scraper extracts the following movie information:
- タイトル (Title)
- 特集名 (Special Feature Name)
- 制作年/国/時間 (Year/Country/Duration)
- 監督/出演 (Director/Cast)
- 概要 (Synopsis)
- 上映スケジュール (Screening Schedule)
- 料金 (Pricing)
- 受賞歴 (Awards)
- イベント情報 (Event Information)
- シネマ名 (Cinema Name)
- ファイル名 (Source Filename)

## HTML Scraping Compatibility

Current scrapers are designed for 下高井戸シネマ (Shimotakaido Cinema) HTML structure:
- Uses `div.box` containers for each movie
- Targets `span.eiga-title` for movie titles
- Supports `span.title-s` for special feature titles
- Processes CSS classes: `.stuff`, `.note`, `.day`, `.price`, `.syo`, `.p3`

**Compatibility Status:**
- ✅ 下高井戸シネマ: 65 movies extracted
- ❌ Other cinemas: Require custom scrapers due to different HTML structures

## Google Sheets Integration

The project includes functionality to upload scraped data to Google Sheets:
- Requires Google Cloud Platform setup with Sheets API enabled
- Uses service account authentication with JSON credentials
- Creates date-stamped worksheets for each scraping session
- Detailed setup instructions available in `doc/manual.md`

## Development Notes

- Main development happens in the Jupyter notebook (`notebook/test.ipynb`)
- HTML scraping scripts provide production-ready tools for batch processing
- The project processes both regular movies and special feature screenings
- HTML parsing is done with BeautifulSoup, targeting specific CSS classes
- Error handling is implemented for robust scraping
- Output is saved as CSV files in the `data/` directory with UTF-8 encoding
- All scripts support Japanese text properly

## Testing and Data

Sample HTML files from various cinema websites are stored in `html/` directory for testing and development purposes. Use `html_analyzer.py` to analyze HTML structure and compatibility before scraping.

## Documentation

- `doc/manual.md`: Comprehensive setup and usage manual
- `doc/scraping_scripts.md`: Japanese documentation for HTML scraping scripts with detailed usage examples