import pandas as pd
from bs4 import BeautifulSoup
import os
import re
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


def scrape_all_html_files(html_dir="html", output_dir="data"):
    if not os.path.exists(html_dir):
        print(f"HTML directory '{html_dir}' not found")
        return pd.DataFrame()
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
    
    if not html_files:
        print(f"No HTML files found in '{html_dir}' directory")
        return pd.DataFrame()
    
    print(f"Found {len(html_files)} HTML files:")
    for file in html_files:
        print(f"  - {file}")
    
    all_data = []
    
    for html_file in html_files:
        file_path = os.path.join(html_dir, html_file)
        print(f"\nProcessing: {html_file}")
        
        try:
            movies_data = scrape_html_file(file_path)
            
            if movies_data:
                df = pd.DataFrame(movies_data)
                columns = ["タイトル", "特集名", "制作年/国/時間", "監督/出演", "概要", "上映スケジュール", "料金", "受賞歴", "イベント情報"]
                df = df.reindex(columns=columns)
                
                cinema_name = html_file.replace('.html', '')
                df['シネマ名'] = cinema_name
                all_data.append(df)
                print(f"  Extracted {len(df)} movies")
                
                output_file = os.path.join(output_dir, f"{cinema_name}.csv")
                df.to_csv(output_file, index=False, encoding="utf-8")
                print(f"  Saved to: {output_file}")
            else:
                print(f"  No movie data found in {html_file}")
                
        except Exception as e:
            print(f"  Error processing {html_file}: {e}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_output = os.path.join(output_dir, f"all_cinemas_{timestamp}.csv")
        combined_df.to_csv(combined_output, index=False, encoding="utf-8")
        print(f"\nCombined data saved to: {combined_output}")
        print(f"Total movies extracted: {len(combined_df)}")
        
        return combined_df
    else:
        print("\nNo data was extracted from any HTML files")
        return pd.DataFrame()


if __name__ == "__main__":
    result_df = scrape_all_html_files()
    
    if not result_df.empty:
        print("\n=== Sample of extracted data ===")
        print(result_df.head().to_string())