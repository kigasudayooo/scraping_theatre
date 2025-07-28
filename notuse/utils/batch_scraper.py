import pandas as pd
from bs4 import BeautifulSoup
import os
import re
import sys
import argparse
from datetime import datetime


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text.strip())
    return text


def process_movie_box(box, is_special=False, special_title=None):
    title_elem = box.find("span", class_="eiga-title")
    stuff_elem = box.find(["p", "span"], class_="stuff")
    note_elem = box.find(["p", "span"], class_="note")
    day_elem = box.find(["p", "span"], class_="day")
    price_elem = box.find("p", class_="price")
    award_elem = box.find("p", class_="syo")
    event_elem = box.find("p", class_="p3")

    if not title_elem:
        return None

    basic_info = ""
    director_cast = ""
    if stuff_elem:
        stuff_text = stuff_elem.text.strip()
        stuff_lines = stuff_text.split("\n")
        basic_info = clean_text(stuff_lines[0]) if stuff_lines else ""
        director_cast = clean_text("\n".join(stuff_lines[1:])) if len(stuff_lines) > 1 else ""

    return {
        "タイトル": clean_text(title_elem.text),
        "特集名": clean_text(special_title) if is_special else "",
        "制作年/国/時間": basic_info,
        "監督/出演": director_cast,
        "概要": clean_text(note_elem.text) if note_elem else "",
        "上映スケジュール": clean_text(day_elem.text) if day_elem else "",
        "料金": clean_text(price_elem.text) if price_elem else "",
        "受賞歴": clean_text(award_elem.text) if award_elem else "",
        "イベント情報": clean_text(event_elem.text) if event_elem else "",
    }


def scrape_html_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    
    soup = BeautifulSoup(html_content, "html.parser")
    movies_data = []
    
    movie_boxes = soup.find_all("div", class_="box")
    
    for box in movie_boxes:
        try:
            title_elem = box.find("span", class_="eiga-title")
            title_s_elem = box.find("span", class_="title-s")
            
            if not title_elem and not title_s_elem:
                continue
            
            title = clean_text(title_elem.text if title_elem else title_s_elem.text)
            
            if title_s_elem:
                details_elem = box.find("details")
                if details_elem:
                    sub_movies = details_elem.find_all("div", class_="box")
                    for sub_movie in sub_movies:
                        sub_title_elem = sub_movie.find("span", class_="eiga-title")
                        if not sub_title_elem:
                            continue
                        movie_info = process_movie_box(sub_movie, is_special=True, special_title=title)
                        if movie_info:
                            movies_data.append(movie_info)
                else:
                    movie_info = process_movie_box(box, is_special=True)
                    if movie_info:
                        movies_data.append(movie_info)
            else:
                movie_info = process_movie_box(box)
                if movie_info:
                    movies_data.append(movie_info)
        
        except Exception as e:
            print(f"Error processing movie: {e}")
    
    return movies_data


def process_files(file_list, output_dir="data", combine=False):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    all_data = []
    processed_count = 0
    
    for file_path in file_list:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
            
        if not file_path.endswith('.html'):
            print(f"Skipping non-HTML file: {file_path}")
            continue
        
        print(f"Processing: {file_path}")
        
        try:
            movies_data = scrape_html_file(file_path)
            
            if movies_data:
                df = pd.DataFrame(movies_data)
                columns = ["タイトル", "特集名", "制作年/国/時間", "監督/出演", "概要", "上映スケジュール", "料金", "受賞歴", "イベント情報"]
                df = df.reindex(columns=columns)
                
                filename = os.path.basename(file_path)
                cinema_name = filename.replace('.html', '')
                df['シネマ名'] = cinema_name
                df['ファイル名'] = filename
                
                all_data.append(df)
                processed_count += 1
                print(f"  Extracted {len(df)} movies")
                
                if not combine:
                    output_file = os.path.join(output_dir, f"{cinema_name}.csv")
                    df.to_csv(output_file, index=False, encoding="utf-8")
                    print(f"  Saved to: {output_file}")
            else:
                print(f"  No movie data found in {file_path}")
                
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
    
    if combine and all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_output = os.path.join(output_dir, f"batch_scraped_{timestamp}.csv")
        combined_df.to_csv(combined_output, index=False, encoding="utf-8")
        print(f"\nCombined data saved to: {combined_output}")
        print(f"Total movies extracted: {len(combined_df)}")
        
        return combined_df
    
    print(f"\nProcessed {processed_count} files successfully")
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description="Batch process HTML files for movie scraping")
    parser.add_argument("files", nargs="+", help="HTML files to process")
    parser.add_argument("-o", "--output", default="data", help="Output directory (default: data)")
    parser.add_argument("-c", "--combine", action="store_true", help="Combine all results into one file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Processing {len(args.files)} files")
        print(f"Output directory: {args.output}")
        print(f"Combine files: {args.combine}")
    
    result_df = process_files(args.files, args.output, args.combine)
    
    if not result_df.empty and args.verbose:
        print("\n=== Sample of extracted data ===")
        print(result_df.head().to_string())


if __name__ == "__main__":
    main()