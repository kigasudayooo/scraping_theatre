import os
import sys
from bs4 import BeautifulSoup
import re
from collections import Counter


def analyze_html_structure(file_path):
    """HTMLファイルの構造を分析"""
    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    analysis = {
        "file_name": os.path.basename(file_path),
        "file_size": len(html_content),
        "title": soup.title.string if soup.title else "No title",
        "total_elements": len(soup.find_all()),
    }
    
    # div.box要素の分析
    movie_boxes = soup.find_all("div", class_="box")
    analysis["movie_boxes_count"] = len(movie_boxes)
    
    # 映画タイトル要素の分析
    title_elements = soup.find_all("span", class_="eiga-title")
    title_s_elements = soup.find_all("span", class_="title-s")
    analysis["eiga_title_count"] = len(title_elements)
    analysis["title_s_count"] = len(title_s_elements)
    
    # その他の重要な要素
    analysis["stuff_elements"] = len(soup.find_all(class_="stuff"))
    analysis["note_elements"] = len(soup.find_all(class_="note"))
    analysis["day_elements"] = len(soup.find_all(class_="day"))
    analysis["price_elements"] = len(soup.find_all("p", class_="price"))
    analysis["award_elements"] = len(soup.find_all("p", class_="syo"))
    analysis["event_elements"] = len(soup.find_all("p", class_="p3"))
    
    # 特集情報
    details_elements = soup.find_all("details")
    analysis["details_count"] = len(details_elements)
    
    # 全クラス名の統計
    all_classes = []
    for element in soup.find_all(class_=True):
        if isinstance(element.get('class'), list):
            all_classes.extend(element.get('class'))
        else:
            all_classes.append(element.get('class'))
    
    class_counter = Counter(all_classes)
    analysis["top_classes"] = dict(class_counter.most_common(10))
    
    return analysis


def extract_sample_content(file_path, max_samples=3):
    """サンプルコンテンツを抽出"""
    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    
    soup = BeautifulSoup(html_content, "html.parser")
    samples = []
    
    movie_boxes = soup.find_all("div", class_="box")[:max_samples]
    
    for i, box in enumerate(movie_boxes):
        sample = {"box_index": i + 1}
        
        # タイトル
        title_elem = box.find("span", class_="eiga-title")
        title_s_elem = box.find("span", class_="title-s")
        if title_elem:
            sample["title"] = title_elem.text.strip()
        elif title_s_elem:
            sample["title"] = title_s_elem.text.strip()
        else:
            sample["title"] = "No title found"
        
        # その他の情報
        stuff_elem = box.find(class_="stuff")
        if stuff_elem:
            sample["stuff"] = stuff_elem.text.strip()[:100] + "..." if len(stuff_elem.text.strip()) > 100 else stuff_elem.text.strip()
        
        note_elem = box.find(class_="note")
        if note_elem:
            sample["note"] = note_elem.text.strip()[:100] + "..." if len(note_elem.text.strip()) > 100 else note_elem.text.strip()
        
        day_elem = box.find(class_="day")
        if day_elem:
            sample["schedule"] = day_elem.text.strip()[:100] + "..." if len(day_elem.text.strip()) > 100 else day_elem.text.strip()
        
        samples.append(sample)
    
    return samples


def analyze_all_html_files(html_dir="html"):
    """htmlディレクトリ内の全HTMLファイルを分析"""
    if not os.path.exists(html_dir):
        print(f"Directory '{html_dir}' not found")
        return
    
    html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
    
    if not html_files:
        print(f"No HTML files found in '{html_dir}' directory")
        return
    
    print(f"=== Analysis of {len(html_files)} HTML files ===\n")
    
    total_analysis = {
        "total_files": len(html_files),
        "total_movie_boxes": 0,
        "total_movies": 0,
        "files_with_content": 0,
    }
    
    for html_file in html_files:
        file_path = os.path.join(html_dir, html_file)
        print(f"--- {html_file} ---")
        
        try:
            analysis = analyze_html_structure(file_path)
            
            print(f"File size: {analysis['file_size']:,} bytes")
            print(f"Title: {analysis['title']}")
            print(f"Movie boxes: {analysis['movie_boxes_count']}")
            print(f"Movie titles (eiga-title): {analysis['eiga_title_count']}")
            print(f"Special titles (title-s): {analysis['title_s_count']}")
            print(f"Details sections: {analysis['details_count']}")
            
            # 統計に追加
            total_analysis["total_movie_boxes"] += analysis["movie_boxes_count"]
            total_analysis["total_movies"] += analysis["eiga_title_count"]
            if analysis["movie_boxes_count"] > 0:
                total_analysis["files_with_content"] += 1
            
            # サンプルコンテンツ
            samples = extract_sample_content(file_path, 2)
            if samples:
                print("Sample content:")
                for sample in samples:
                    print(f"  [{sample['box_index']}] {sample['title']}")
                    if 'schedule' in sample:
                        print(f"      Schedule: {sample['schedule']}")
            
            print()
            
        except Exception as e:
            print(f"Error analyzing {html_file}: {e}\n")
    
    print("=== Summary ===")
    print(f"Total files: {total_analysis['total_files']}")
    print(f"Files with movie content: {total_analysis['files_with_content']}")
    print(f"Total movie boxes: {total_analysis['total_movie_boxes']}")
    print(f"Total movie titles: {total_analysis['total_movies']}")


def analyze_single_file(file_path, detailed=False):
    """単一ファイルの詳細分析"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    print(f"=== Detailed Analysis: {os.path.basename(file_path)} ===\n")
    
    analysis = analyze_html_structure(file_path)
    
    print("Basic Information:")
    for key, value in analysis.items():
        if key != "top_classes":
            print(f"  {key}: {value}")
    
    print(f"\nTop CSS classes:")
    for class_name, count in analysis["top_classes"].items():
        print(f"  {class_name}: {count}")
    
    if detailed:
        print(f"\nSample content:")
        samples = extract_sample_content(file_path, 5)
        for sample in samples:
            print(f"\n--- Box {sample['box_index']} ---")
            for key, value in sample.items():
                if key != "box_index":
                    print(f"{key}: {value}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python html_analyzer.py all                    # Analyze all HTML files in html/ directory")
        print("  python html_analyzer.py <file_path>            # Analyze single file")
        print("  python html_analyzer.py <file_path> detailed   # Detailed analysis of single file")
        sys.exit(1)
    
    if sys.argv[1] == "all":
        analyze_all_html_files()
    else:
        file_path = sys.argv[1]
        detailed = len(sys.argv) > 2 and sys.argv[2] == "detailed"
        analyze_single_file(file_path, detailed)


if __name__ == "__main__":
    main()