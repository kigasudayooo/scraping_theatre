# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with this Japanese cinema web scraping and Discord bot project.

## Project Overview

A comprehensive system combining web scraping of Japanese cinema websites with Discord bot integration for automated notifications and interactive movie information queries. The project extracts structured movie data, schedules, and theater information, then provides weekly Discord notifications and on-demand movie searches.

**Key Features:**
- **Web Scraping**: Multi-theater HTML parsing with object-oriented architecture
- **Discord Integration**: Weekly notifications and interactive movie queries
- **Data Management**: Structured data models with CSV export and Google Sheets integration
- **Scalable Architecture**: Abstract base classes for easy theater expansion
- **Japanese Text Support**: Proper encoding and formatting for Japanese content

## Technology Stack

### Core Dependencies
- **Python**: >=3.11 (managed with uv)
- **Web Scraping**: BeautifulSoup4, Selenium, Requests
- **Data Processing**: Pandas for CSV export and data manipulation
- **Discord Integration**: discord.py for bot functionality
- **Development**: Jupyter for interactive development
- **APIs**: gspread + oauth2client for Google Sheets integration

### Development Environment Setup
```bash
# Install all dependencies
uv sync

# Verify installation
uv run python --version
uv run python -c "import pandas, bs4, discord; print('Dependencies OK')"
```

## Project Architecture

```
scraping_theatre/
├── 📚 **Root Level**
│   ├── README.md                    # Project overview
│   ├── CLAUDE.md                    # Claude instructions
│   ├── pyproject.toml              # Python configuration
│   ├── uv.lock                     # Dependency lock
│   ├── run_scraping.py            # Scraping execution
│   └── run_discord_bot.py         # Discord Bot execution
│
├── 📦 **src/ - Source Code**
│   ├── scraping/                   # Scraping module
│   │   ├── models.py              # Data models (MovieInfo, TheaterInfo, etc.)
│   │   ├── base_scraper.py        # Abstract base scraper class
│   │   ├── main.py                # TheaterScrapingOrchestrator
│   │   └── scrapers/              # Theater-specific implementations
│   │       ├── ks_cinema_scraper.py
│   │       ├── pole_pole_scraper.py
│   │       ├── eurospace_scraper.py
│   │       ├── shimotakaido_scraper.py
│   │       ├── waseda_shochiku_scraper.py
│   │       └── shinjuku_musashino_scraper.py
│   │
│   ├── discord_bot/               # Discord Bot module
│   │   ├── discord_bot_main.py    # CombinedMovieBot (main implementation)
│   │   ├── weekly_notifier.py     # Weekly notification system
│   │   ├── interactive_bot.py     # Interactive query handling
│   │   ├── discord_config.py      # Configuration management
│   │   └── discord_models.py      # Discord-specific data models
│   │
│   └── utils/                     # Legacy utilities
│       ├── html_analyzer.py       # HTML structure analysis
│       ├── batch_scraper.py       # Batch processing
│       ├── scrape_all_html.py     # Legacy batch processor
│       └── scrape_single_html.py  # Legacy single processor
│
├── 📖 **docs/ - Documentation**
│   ├── DISCORD_BOT_SETUP_GUIDE.md # Comprehensive Discord setup guide
│   └── scraping_scripts.md       # Japanese documentation
│
├── ⚙️ **config/ - Configuration**
│   └── .env.example              # Environment variables template
│
├── 📊 **data/ - Data Storage**    # Generated CSV files
├── 📝 **logs/ - Log Files**       # Bot and scraping logs
└── 📄 **html/ - Reference HTML**  # Sample HTML files for testing
```

## Core System Components

### 1. Web Scraping System

**Main Execution:**
```bash
# Scrape all theaters
python run_scraping.py all

# Scrape specific theater
python run_scraping.py ks_cinema
```

**Architecture:**
- `BaseScraper`: Abstract base class with common HTTP/Selenium functionality
- Theater-specific scrapers inherit from `BaseScraper`
- `TheaterScrapingOrchestrator`: Manages all scrapers and data collection
- Data models: `MovieInfo`, `TheaterInfo`, `ShowtimeInfo`, `MovieSchedule`, `TheaterData`

### 2. Discord Bot System

**Main Execution:**
```bash
# Run combined Discord bot
python run_discord_bot.py
```

**Features:**
- **Weekly Notifications**: Every Monday 7:30 AM with current/upcoming movies
- **Interactive Queries**: Movie search, theater schedules, director works
- **Playwright Integration**: Enhanced external movie information search
- **Multi-channel Support**: Main notifications and detailed Q&A channels

**Bot Commands:**
- `!help` - Display help information
- `!status` - Show bot status and configuration
- `!update` - Manual data refresh

## Discord Bot Setup

### Environment Variables Required
```bash
# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_MAIN_CHANNEL_NAME=weekly-movies
DISCORD_DETAIL_CHANNEL_NAME=movie-questions

# Optional Settings
ENABLE_PLAYWRIGHT_SEARCH=true
WEEKLY_REPORT_TIME=MON 07:30
TIMEZONE=Asia/Tokyo
```

### Bot Permissions Required
- Send Messages
- Use Slash Commands
- Embed Links
- Read Message History
- Add Reactions

For detailed setup instructions, see `docs/DISCORD_BOT_SETUP_GUIDE.md`.

## Data Models

### Core Data Structures
```python
@dataclass
class MovieInfo:
    title: str
    director: Optional[str] = None
    cast: List[str] = field(default_factory=list)
    genre: Optional[str] = None
    duration: Optional[int] = None
    synopsis: Optional[str] = None
    poster_url: Optional[str] = None

@dataclass
class TheaterInfo:
    name: str
    url: str
    address: Optional[str] = None
    phone: Optional[str] = None

@dataclass
class ShowtimeInfo:
    date: str  # YYYY-MM-DD format
    times: List[str]  # ["14:30", "19:00"]
    screen: Optional[str] = None
    ticket_url: Optional[str] = None
```

## Supported Theaters

| Theater | Status | Features |
|---------|--------|----------|
| ケイズシネマ (Ks Cinema) | ✅ Full Support | Movies, schedules, theater info |
| ポレポレ東中野 (Pole Pole) | ✅ Full Support | Movies, schedules, theater info |
| ユーロスペース (Eurospace) | ✅ Full Support | Movies, schedules, theater info |
| 下高井戸シネマ (Shimotakaido) | ✅ Full Support | Movies, schedules, theater info |
| 早稲田松竹 (Waseda Shochiku) | ✅ Full Support | Movies, schedules, theater info |
| 新宿武蔵野館 (Shinjuku Musashino) | ✅ Full Support | Movies, schedules, theater info |

## Discord Bot Usage Examples

### Weekly Notifications
Automatically sent every Monday 7:30 AM:
```
🎬 【今週・来週の上映映画】7/8〜7/14
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎭 『映画タイトル』
📍 上映館: ケイズシネマ, ポレポレ東中野
📅 期間: 7/8(月)〜7/14(日)
💭 あらすじ...

📊 合計: 25作品 | 6映画館
🤖 詳細情報は #映画-質問 で質問してください
```

### Interactive Queries
In the `#movie-questions` channel:
- **映画情報**: "「映画タイトル」について教えて"
- **映画館スケジュール**: "ケイズシネマの今週の上映予定は？"
- **監督作品**: "監督「監督名」の作品を教えて"

## Development Workflow

### 1. Adding New Theater Support
```bash
# Create new scraper class
touch src/scraping/scrapers/new_theater_scraper.py

# Implement scraper inheriting from BaseScraper
class NewTheaterScraper(BaseScraper):
    def get_movies(self) -> List[MovieInfo]:
        # Implementation
    
    def get_schedules(self) -> List[MovieSchedule]:
        # Implementation

# Register in main.py orchestrator
```

### 2. Testing and Validation
```bash
# Test specific scraper
uv run python -c "from src.scraping.scrapers.ks_cinema_scraper import KsCinemaScraper; print('Import OK')"

# Test Discord bot
uv run python -c "from src.discord_bot.discord_config import load_config; print('Discord OK')"

# Run full system test
python run_scraping.py all
```

### 3. Discord Bot Development
```bash
# Test bot configuration
uv run python -c "from src.discord_bot.discord_config import load_config; config = load_config(); print(f'Config loaded: {bool(config[0].token)}')"

# Run bot locally for testing
python run_discord_bot.py
```

## Error Handling and Logging

### Logging Configuration
- All components use Python's `logging` module
- Logs written to `logs/` directory
- Discord bot logs include user interactions and errors
- Scraping logs include HTTP errors and parsing issues

### Common Issues and Solutions

**Import Errors:**
- Ensure all imports use relative paths within src/ modules
- Check that `__init__.py` files exist in all package directories

**Discord Bot Issues:**
- Verify bot token and permissions
- Check channel names match configuration
- Review Discord API rate limits

**Scraping Failures:**
- Check internet connectivity and target site availability
- Review site structure changes requiring scraper updates
- Verify Selenium WebDriver installation

## Deployment

### Local Development
```bash
# Install dependencies
uv sync

# Run scraping system
python run_scraping.py all

# Run Discord bot
python run_discord_bot.py
```

### Production Deployment
- Set environment variables in `.env` file
- Configure systemd service for continuous Discord bot operation
- Set up cron job for periodic data updates
- Monitor system resources and implement temperature-based shutdown for mini PC deployments

## Extension Points

### Adding New Data Sources
1. Create scraper class inheriting from `BaseScraper`
2. Implement required abstract methods
3. Register in `TheaterScrapingOrchestrator`
4. Add theater info to supported theaters list

### Discord Bot Features
1. Add new query patterns to `MovieQueryParser`
2. Implement corresponding handlers in `InteractiveBot`
3. Create embed templates for new response types
4. Test with Discord bot commands

This system provides a solid foundation for Japanese cinema data collection and Discord-based user interaction, with clear extension points for adding new theaters and features.