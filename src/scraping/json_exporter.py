"""
JSON Export Functionality for Cinema Scraping System

This module provides functionality to export scraped cinema data to JSON format
for integration with the Ollama-powered Discord bot system.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import TheaterData, CinemaDatabase

logger = logging.getLogger(__name__)

class CinemaJSONExporter:
    """映画館データのJSON出力クラス"""
    
    def __init__(self, output_dir: str = "data"):
        """
        Initialize JSON exporter
        
        Args:
            output_dir: Output directory for JSON files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def export_cinema_database(
        self, 
        theater_data_list: List[TheaterData], 
        filename: str = "movies_data.json"
    ) -> str:
        """
        Export complete cinema database to JSON
        
        Args:
            theater_data_list: List of theater data to export
            filename: Output filename (default: movies_data.json)
            
        Returns:
            Path to the exported JSON file
        """
        try:
            # Create cinema database from theater data
            cinema_db = CinemaDatabase.from_theater_data_list(theater_data_list)
            
            # Generate output path
            output_path = self.output_dir / filename
            
            # Save to JSON file
            cinema_db.save_to_file(str(output_path))
            
            logger.info(f"Successfully exported cinema database to {output_path}")
            logger.info(f"Total theaters: {len(cinema_db.theaters)}")
            logger.info(f"Total movies: {cinema_db.summary.get('total_movies', 0)}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to export cinema database: {e}")
            raise
    
    def export_individual_theaters(
        self, 
        theater_data_list: List[TheaterData]
    ) -> Dict[str, str]:
        """
        Export individual theater data to separate JSON files
        
        Args:
            theater_data_list: List of theater data to export
            
        Returns:
            Dictionary mapping theater names to their JSON file paths
        """
        exported_files = {}
        
        for theater_data in theater_data_list:
            if not theater_data.movies:
                logger.warning(f"No movies found for {theater_data.theater_info.name}, skipping")
                continue
                
            try:
                # Generate filename from theater name
                theater_name = theater_data.theater_info.name
                safe_name = theater_name.lower().replace(' ', '_').replace('（', '').replace('）', '')
                filename = f"{safe_name}.json"
                output_path = self.output_dir / filename
                
                # Convert to JSON-friendly format
                theater_json_data = {
                    "theater_info": theater_data.theater_info.__dict__,
                    "movies": [movie.__dict__ for movie in theater_data.movies],
                    "schedules": [
                        {
                            "theater_name": schedule.theater_name,
                            "movie_title": schedule.movie_title,
                            "showtimes": [showtime.__dict__ for showtime in schedule.showtimes]
                        }
                        for schedule in theater_data.schedules
                    ],
                    "exported_at": datetime.now().isoformat()
                }
                
                # Save to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(theater_json_data, f, ensure_ascii=False, indent=2)
                
                exported_files[theater_name] = str(output_path)
                logger.info(f"Exported {theater_name} to {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to export {theater_data.theater_info.name}: {e}")
                continue
        
        return exported_files
    
    def load_cinema_database(self, filename: str = "movies_data.json") -> Optional[Dict[str, Any]]:
        """
        Load cinema database from JSON file
        
        Args:
            filename: JSON filename to load
            
        Returns:
            Loaded cinema database data or None if failed
        """
        try:
            file_path = self.output_dir / filename
            
            if not file_path.exists():
                logger.warning(f"JSON file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Successfully loaded cinema database from {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load cinema database: {e}")
            return None
    
    def get_latest_data_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the latest exported data
        
        Returns:
            Information about the latest data or None if no data found
        """
        try:
            json_file = self.output_dir / "movies_data.json"
            
            if not json_file.exists():
                return None
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                "last_updated": data.get("last_updated"),
                "total_theaters": len(data.get("theaters", {})),
                "total_movies": data.get("summary", {}).get("total_movies", 0),
                "active_theaters": data.get("summary", {}).get("active_theaters", 0),
                "file_size": json_file.stat().st_size,
                "file_path": str(json_file)
            }
            
        except Exception as e:
            logger.error(f"Failed to get latest data info: {e}")
            return None

def export_theater_data_to_json(
    theater_data_list: List[TheaterData], 
    output_dir: str = "data",
    individual_files: bool = False
) -> Dict[str, str]:
    """
    Convenience function to export theater data to JSON
    
    Args:
        theater_data_list: List of theater data to export
        output_dir: Output directory for JSON files
        individual_files: Whether to create individual files per theater
        
    Returns:
        Dictionary of exported file paths
    """
    exporter = CinemaJSONExporter(output_dir)
    
    exported_files = {}
    
    # Export main database
    main_file = exporter.export_cinema_database(theater_data_list)
    exported_files["main_database"] = main_file
    
    # Export individual files if requested
    if individual_files:
        individual_files_dict = exporter.export_individual_theaters(theater_data_list)
        exported_files.update(individual_files_dict)
    
    return exported_files