#!/usr/bin/env python3
"""
ハイブリッドシステムのプロトタイプ実装
段階的フォールバック: プログラム → LLM → データ検索 → テンプレート出力
"""

import json
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class HybridCinemaSystem:
    """ハイブリッド映画情報システム"""
    
    def __init__(self, data_file: str = "data/movies_data.json"):
        self.data = self._load_data(data_file)
        
        # プログラム型パターン
        self.date_patterns = {
            r'今日': 0,
            r'明日': 1,
            r'明後日': 2,
            r'昨日': -1,
            r'(\d{1,2})月(\d{1,2})日': 'specific_date',
            r'(\d{4})-(\d{1,2})-(\d{1,2})': 'iso_date'
        }
        
        self.theater_exact_patterns = [
            r'(ケイズシネマ|下高井戸シネマ|早稲田松竹|新宿武蔵野館)',
        ]
        
        self.movie_patterns = [
            r'「(.+?)」',
            r'『(.+?)』'
        ]
        
        # 劇場名正規化辞書
        self.theater_aliases = {
            'ケイズ': 'ケイズシネマ',
            'k\'s': 'ケイズシネマ',
            'ks': 'ケイズシネマ',
            '下高井戸': '下高井戸シネマ',
            'しもたか': '下高井戸シネマ',
            'シモタカ': '下高井戸シネマ',
            '早稲田': '早稲田松竹',
            '松竹': '早稲田松竹',
            '武蔵野': '新宿武蔵野館',
            '武蔵野館': '新宿武蔵野館'
        }
    
    def _load_data(self, data_file: str) -> Dict:
        """データ読み込み"""
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"データファイルが見つかりません: {data_file}")
            return {"theaters": {}}
    
    def extract_keywords_programmatic(self, query: str) -> Dict[str, List[str]]:
        """プログラム型キーワード抽出（確実だが限定的）"""
        result = {'dates': [], 'theaters': [], 'movies': []}
        
        today = date.today()
        
        # 日付抽出
        for pattern, offset in self.date_patterns.items():
            if isinstance(offset, int):
                if re.search(pattern, query):
                    target_date = today + timedelta(days=offset)
                    result['dates'].append(target_date.strftime('%Y-%m-%d'))
            elif offset == 'specific_date':
                matches = re.findall(pattern, query)
                for month, day in matches:
                    try:
                        target_date = date(today.year, int(month), int(day))
                        result['dates'].append(target_date.strftime('%Y-%m-%d'))
                    except ValueError:
                        pass
        
        # 劇場抽出（厳密一致）
        for pattern in self.theater_exact_patterns:
            matches = re.findall(pattern, query)
            result['theaters'].extend(matches)
        
        # 映画抽出
        for pattern in self.movie_patterns:
            matches = re.findall(pattern, query)
            result['movies'].extend(matches)
        
        return result
    
    def extract_keywords_llm_simulation(self, query: str) -> Dict[str, List[str]]:
        """LLM型キーワード抽出のシミュレーション（実際の実装では本物のLLMを呼び出し）"""
        result = {'dates': [], 'theaters': [], 'movies': []}
        
        # 複雑な日付表現（LLMが理解できる）
        today = date.today()
        
        # 相対日付の理解
        if 'この週末' in query:
            # 今週の土日を計算
            days_until_saturday = (5 - today.weekday()) % 7
            saturday = today + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            result['dates'].extend([saturday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')])
        
        if '来週' in query:
            next_week_start = today + timedelta(days=(7 - today.weekday()))
            for i in range(7):
                result['dates'].append((next_week_start + timedelta(days=i)).strftime('%Y-%m-%d'))
        
        if '今月末' in query:
            # 月末の日付
            next_month = today.replace(day=28) + timedelta(days=4)
            month_end = next_month - timedelta(days=next_month.day)
            result['dates'].append(month_end.strftime('%Y-%m-%d'))
        
        # 劇場名の柔軟な理解
        query_lower = query.lower()
        for alias, official in self.theater_aliases.items():
            if alias.lower() in query_lower:
                result['theaters'].append(official)
        
        # 映画名抽出（プログラム型と同じ）
        for pattern in self.movie_patterns:
            matches = re.findall(pattern, query)
            result['movies'].extend(matches)
        
        return result
    
    def extract_keywords(self, query: str) -> Tuple[Dict[str, List[str]], str]:
        """
        段階的フォールバック方式でキーワード抽出
        
        Returns:
            Tuple[抽出結果, 使用した方法]
        """
        # Step 1: プログラム型で試行
        prog_result = self.extract_keywords_programmatic(query)
        prog_total = len(prog_result['dates']) + len(prog_result['theaters']) + len(prog_result['movies'])
        
        if prog_total > 0:
            return prog_result, "programmatic"
        
        # Step 2: プログラム型で不十分な場合、LLM型を使用
        llm_result = self.extract_keywords_llm_simulation(query)
        llm_total = len(llm_result['dates']) + len(llm_result['theaters']) + len(llm_result['movies'])
        
        if llm_total > 0:
            return llm_result, "llm_fallback"
        
        # Step 3: 両方とも失敗
        return {'dates': [], 'theaters': [], 'movies': []}, "failed"
    
    def search_by_date(self, target_date: str) -> Dict[str, List[Dict]]:
        """指定日付の全劇場の映画を検索"""
        results = {}
        
        for theater_name, theater_data in self.data.get("theaters", {}).items():
            movies_on_date = []
            
            for movie in theater_data.get("movies", []):
                for schedule in movie.get("schedules", []):
                    if schedule.get("date") == target_date:
                        movies_on_date.append({
                            "title": movie.get("title"),
                            "times": schedule.get("times", []),
                            "screen": schedule.get("screen", "")
                        })
            
            if movies_on_date:
                results[theater_name] = movies_on_date
        
        return results
    
    def search_theater_movies(self, theater_name: str) -> Optional[Dict]:
        """劇場の全映画を検索"""
        theater_data = self.data.get("theaters", {}).get(theater_name)
        if theater_data:
            return theater_data
        return None
    
    def search_movie_info(self, movie_name: str) -> Optional[Dict]:
        """映画情報を検索"""
        for theater_name, theater_data in self.data.get("theaters", {}).items():
            for movie in theater_data.get("movies", []):
                if movie_name.lower() in movie.get("title", "").lower():
                    return {
                        "movie": movie,
                        "theater": theater_name,
                        "theater_data": theater_data
                    }
        return None
    
    def format_date_response(self, target_date: str, results: Dict[str, List[Dict]]) -> str:
        """日付検索結果を整形"""
        if not results:
            return f"{target_date}の上映予定は見つかりませんでした。"
        
        # 日付を読みやすい形式に変換
        try:
            date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%m月%d日(%a)')
        except:
            formatted_date = target_date
        
        response = f"■ {formatted_date}の上映予定\n\n"
        
        for theater_name, movies in results.items():
            response += f"【{theater_name}】\n"
            for movie in movies:
                times_str = "、".join(movie['times'])
                screen_str = f" [{movie['screen']}]" if movie['screen'] else ""
                response += f"・{movie['title']}: {times_str}{screen_str}\n"
            response += "\n"
        
        return response
    
    def format_theater_response(self, theater_data: Dict, theater_name: str) -> str:
        """劇場検索結果を整形"""
        response = f"■ {theater_name}\n"
        response += f"・住所: {theater_data.get('address', '情報なし')}\n"
        response += f"・URL: {theater_data.get('url', '情報なし')}\n\n"
        
        movies = theater_data.get('movies', [])
        response += f"■ 上映中の映画（{len(movies)}本）\n\n"
        
        for movie in movies:
            title = movie.get('title', '不明')
            response += f"【{title}】\n"
            
            schedules = movie.get('schedules', [])
            if schedules:
                for schedule in schedules:
                    date_str = schedule.get('date', '')
                    times = schedule.get('times', [])
                    screen = schedule.get('screen', '')
                    
                    if date_str and times:
                        times_str = "、".join(times)
                        screen_str = f" [{screen}]" if screen else ""
                        response += f"・{date_str}: {times_str}{screen_str}\n"
            else:
                response += "・上映スケジュール: 情報なし\n"
            response += "\n"
        
        return response
    
    def format_movie_response(self, movie_info: Dict) -> str:
        """映画検索結果を整形"""
        movie = movie_info["movie"]
        theater = movie_info["theater"]
        
        response = f"■ 映画情報\n"
        response += f"・タイトル: {movie.get('title', '不明')}\n"
        response += f"・監督: {movie.get('director') or '情報なし'}\n"
        response += f"・劇場: {theater}\n\n"
        
        response += f"■ 上映スケジュール\n"
        schedules = movie.get('schedules', [])
        if schedules:
            for schedule in schedules:
                date_str = schedule.get('date', '')
                times = schedule.get('times', [])
                screen = schedule.get('screen', '')
                
                if date_str and times:
                    times_str = "、".join(times)
                    screen_str = f" [{screen}]" if screen else ""
                    response += f"・{date_str}: {times_str}{screen_str}\n"
        else:
            response += "・情報なし\n"
        
        return response
    
    def process_query(self, query: str) -> str:
        """
        クエリを処理して回答を生成
        
        Args:
            query: ユーザーの質問
            
        Returns:
            整形された回答文字列
        """
        print(f"DEBUG: 処理中のクエリ: {query}")
        
        # Step 1: キーワード抽出
        keywords, method = self.extract_keywords(query)
        print(f"DEBUG: 抽出方法: {method}")
        print(f"DEBUG: 抽出結果: {keywords}")
        
        # Step 2: データ検索と回答生成
        
        # 日付検索を優先
        if keywords['dates']:
            for target_date in keywords['dates']:
                results = self.search_by_date(target_date)
                if results:
                    return self.format_date_response(target_date, results)
        
        # 映画検索
        if keywords['movies']:
            for movie_name in keywords['movies']:
                movie_info = self.search_movie_info(movie_name)
                if movie_info:
                    return self.format_movie_response(movie_info)
        
        # 劇場検索
        if keywords['theaters']:
            for theater_name in keywords['theaters']:
                theater_data = self.search_theater_movies(theater_name)
                if theater_data:
                    return self.format_theater_response(theater_data, theater_name)
        
        # 該当なし
        return self._format_no_match_response(query, keywords, method)
    
    def _format_no_match_response(self, query: str, keywords: Dict, method: str) -> str:
        """該当なしの場合の応答"""
        response = "申し訳ございませんが、お探しの情報が見つかりませんでした。\n\n"
        response += f"検索方法: {method}\n"
        response += f"抽出されたキーワード: {keywords}\n\n"
        response += "対応している検索:\n"
        response += "・日付: 今日、明日、8月1日など\n"
        response += "・劇場: ケイズシネマ、下高井戸シネマ、早稲田松竹、新宿武蔵野館\n"
        response += "・映画: 「タイトル」で囲んで指定\n"
        
        return response


def main():
    """テスト実行"""
    system = HybridCinemaSystem()
    
    test_queries = [
        "今日の映画は？",
        "明日ケイズシネマで何やってる？", 
        "7月29日の上映予定は？",
        "「また逢いましょう」の上映時間は？",
        "この週末に観られる映画は？",
        "K'sの映画教えて",
        "しもたかで今月末に何かある？"
    ]
    
    print("=" * 70)
    print("ハイブリッドシステム - プロトタイプテスト")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\n【質問】: {query}")
        print("-" * 50)
        response = system.process_query(query)
        print(response)
        print("-" * 50)


if __name__ == "__main__":
    main()