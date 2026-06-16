#!/usr/bin/env python3
"""
Enhanced scraping script with JSON output support

This script extends the existing scraping functionality to include JSON export
for integration with the Ollama-powered Discord bot system.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scraping.json_exporter import CinemaJSONExporter
from src.scraping.scrapers.ks_cinema_scraper import KsCinemaScraper
from src.scraping.scrapers.shimotakaido_scraper import ShimotakaidoCinemaScraper
from src.scraping.scrapers.waseda_shochiku_scraper import WasedaShochikuScraper
from src.scraping.scrapers.shinjuku_musashino_scraper import ShinjukuMusashinoScraper
from src.scraping.scrapers.eurospace_scraper import EurospaceScraper
from src.scraping.scrapers.pole_pole_scraper import PolePoleHigashinakanoScraper


def setup_logging(verbose: bool = False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('scraping.log', encoding='utf-8')
        ]
    )


def main():
    """Main execution function"""
    # Handle command line arguments
    if len(sys.argv) > 1:
        theater_arg = sys.argv[1].lower()
    else:
        theater_arg = "all"
    
    # Setup logging
    setup_logging(verbose=True)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🎬 Starting cinema scraping with JSON support...")
        
        # Initialize available scrapers
        scrapers = {
            'ks_cinema': KsCinemaScraper(),
            'shimotakaido': ShimotakaidoCinemaScraper(),
            'waseda_shochiku': WasedaShochikuScraper(),
            'shinjuku_musashino': ShinjukuMusashinoScraper(),
            'eurospace': EurospaceScraper(),
            'pole_pole': PolePoleHigashinakanoScraper()
        }
        
        theater_data_list = []
        
        # Execute scraping
        if theater_arg == "all":
            logger.info("Scraping all theaters...")
            for theater_name, scraper in scrapers.items():
                try:
                    logger.info(f"Scraping {scraper.__class__.__name__}...")
                    theater_data = scraper.scrape_all()
                    if theater_data and theater_data.movies:
                        theater_data_list.append(theater_data)
                        logger.info(f"✅ {scraper.__class__.__name__}: {len(theater_data.movies)} movies found")
                    else:
                        logger.warning(f"⚠️ {scraper.__class__.__name__}: No movies found")
                except Exception as e:
                    logger.error(f"❌ Failed to scrape {theater_name}: {e}")
        else:
            # Single theater scraping
            if theater_arg in scrapers:
                scraper = scrapers[theater_arg]
                try:
                    logger.info(f"Scraping {scraper.__class__.__name__}...")
                    theater_data = scraper.scrape_all()
                    if theater_data and theater_data.movies:
                        theater_data_list.append(theater_data)
                        logger.info(f"✅ {scraper.__class__.__name__}: {len(theater_data.movies)} movies found")
                    else:
                        logger.warning(f"⚠️ {scraper.__class__.__name__}: No movies found")
                except Exception as e:
                    logger.error(f"❌ Failed to scrape {theater_arg}: {e}")
            else:
                logger.error(f"Unknown theater: {theater_arg}")
                logger.info(f"Available theaters: {list(scrapers.keys())}")
                return 1
        
        if not theater_data_list:
            logger.error("No theater data was scraped successfully")
            return 1
        
        # Export to JSON
        logger.info("📊 Exporting to JSON format...")
        exporter = CinemaJSONExporter("data")
        output_file = exporter.export_cinema_database(theater_data_list)
        
        # Report results
        logger.info("✅ Scraping completed successfully!")
        logger.info(f"📁 JSON file created: {output_file}")
        
        # Load and display summary
        try:
            data = exporter.load_cinema_database()
            if data and 'summary' in data:
                summary = data['summary']
                logger.info("📈 Data Summary:")
                logger.info(f"   Total theaters: {summary.get('total_theaters', 0)}")
                logger.info(f"   Active theaters: {summary.get('active_theaters', 0)}")
                logger.info(f"   Total movies: {summary.get('total_movies', 0)}")
                logger.info(f"   Generated at: {summary.get('generated_at', 'Unknown')}")
        except Exception as e:
            logger.warning(f"Could not load summary: {e}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error during scraping: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)