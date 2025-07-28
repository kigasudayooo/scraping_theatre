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

from src.scraping.main import TheaterScrapingOrchestrator
from src.scraping.json_exporter import CinemaJSONExporter, export_theater_data_to_json


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
    parser = argparse.ArgumentParser(
        description="Cinema scraping with JSON output support"
    )
    parser.add_argument(
        "--output-dir", 
        default="data", 
        help="Output directory for JSON files (default: data)"
    )
    parser.add_argument(
        "--json-only", 
        action="store_true", 
        help="Only output JSON (skip CSV)"
    )
    parser.add_argument(
        "--individual-files", 
        action="store_true", 
        help="Create individual JSON files per theater"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--theaters", 
        nargs="*", 
        help="Specific theaters to scrape (default: all)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🎬 Starting cinema scraping with JSON support...")
        
        # Initialize orchestrator
        orchestrator = TheaterScrapingOrchestrator()
        
        # Scrape theaters - get raw TheaterData objects directly
        if args.theaters:
            logger.info(f"Scraping specific theaters: {args.theaters}")
            theater_data_list = []
            for theater_name in args.theaters:
                if theater_name not in orchestrator.scrapers:
                    logger.error(f"Unknown theater: {theater_name}")
                    continue
                scraper = orchestrator.scrapers[theater_name]
                try:
                    logger.info(f"Scraping {scraper.theater_name}...")
                    theater_data = scraper.scrape_all()
                    theater_data_list.append(theater_data)
                except Exception as e:
                    logger.error(f"Failed to scrape {theater_name}: {e}")
        else:
            logger.info("Scraping all theaters...")
            theater_data_list = []
            for theater_name, scraper in orchestrator.scrapers.items():
                try:
                    logger.info(f"Scraping {scraper.theater_name}...")
                    theater_data = scraper.scrape_all()
                    theater_data_list.append(theater_data)
                except Exception as e:
                    logger.error(f"Failed to scrape {theater_name}: {e}")
        
        if not theater_data_list:
            logger.error("No theater data was scraped successfully")
            return 1
        
        # Export to JSON
        logger.info("📊 Exporting to JSON format...")
        exported_files = export_theater_data_to_json(
            theater_data_list,
            output_dir=args.output_dir,
            individual_files=args.individual_files
        )
        
        # Report results
        logger.info("✅ Scraping completed successfully!")
        logger.info(f"📁 Exported files:")
        for file_type, file_path in exported_files.items():
            logger.info(f"   {file_type}: {file_path}")
        
        # Get summary information
        exporter = CinemaJSONExporter(args.output_dir)
        data_info = exporter.get_latest_data_info()
        
        if data_info:
            logger.info("📈 Data Summary:")
            logger.info(f"   Total theaters: {data_info['total_theaters']}")
            logger.info(f"   Active theaters: {data_info['active_theaters']}")
            logger.info(f"   Total movies: {data_info['total_movies']}")
            logger.info(f"   Last updated: {data_info['last_updated']}")
            logger.info(f"   File size: {data_info['file_size']:,} bytes")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error during scraping: {e}")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)