# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a theatre/cinema web scraping project focused on extracting movie schedule information from Japanese cinema websites, specifically 下高井戸シネマ (Shimotakaido Cinema). The project scrapes movie information including titles, schedules, directors, cast, and event details, then uploads the data to Google Sheets for management.

## Development Environment

### Python Environment
- Uses uv for dependency management
- Python >=3.11 required
- Main dependencies: beautifulsoup4, pandas, jupyter, ipykernel

### Common Commands
```bash
# Install dependencies
uv sync

# Run the main script
python hello.py

# Start Jupyter for development
jupyter notebook
```

## Project Structure

### Core Components
- `hello.py`: Entry point script
- `notebook/test.ipynb`: Main development notebook containing scraping logic
- `doc/manual.md`: Comprehensive manual with setup instructions and code documentation
- `data/`: Output directory for scraped data (CSV files)
- `html/`: Sample HTML files from various cinema websites

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

## Google Sheets Integration

The project includes functionality to upload scraped data to Google Sheets:
- Requires Google Cloud Platform setup with Sheets API enabled
- Uses service account authentication with JSON credentials
- Creates date-stamped worksheets for each scraping session
- Detailed setup instructions available in `doc/manual.md`

## Development Notes

- Main development happens in the Jupyter notebook (`notebook/test.ipynb`)
- The project processes both regular movies and special feature screenings
- HTML parsing is done with BeautifulSoup, targeting specific CSS classes
- Error handling is implemented for robust scraping
- Output is saved as CSV files in the `data/` directory

## Testing and Data

Sample HTML files from various cinema websites are stored in `html/` directory for testing and development purposes.