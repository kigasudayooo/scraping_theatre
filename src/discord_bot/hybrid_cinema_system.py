#!/usr/bin/env python3
"""
完全なハイブリッド映画情報システム
キーワード抽出 + データ検索 + テンプレート出力によるハルシネーション完全防止
"""

import json
import sys
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# 既存モジュールのインポート
sys.path.insert(0, str(Path(__file__).parent))
from hybrid_keyword_extractor import HybridKeywordExtractor
from ollama_client import OllamaClient

class CinemaDataSearcher:
    """映画データ検索エンジン"""
    
    def __init__(self, data_file: str = "data/movies_data.json"):
        """
        初期化
        
        Args:
            data_file: 映画データJSONファイルのパス
        """
        self.data_file = Path(__file__).parent.parent.parent / data_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """映画データを読み込み"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"データファイルが見つかりません: {self.data_file}")
            return {"theaters": {}}
    
    def search_by_date(self, target_date: str, theater_filter: Optional[str] = None, time_filter: Optional[str] = None) -> Dict[str, List[Dict]]:
        """指定日付の映画を検索（劇場・時間フィルタ対応）"""
        results = {}
        
        theaters_to_search = self.data.get("theaters", {})
        
        # 劇場フィルタが指定されている場合
        if theater_filter:
            if theater_filter in theaters_to_search:
                theaters_to_search = {theater_filter: theaters_to_search[theater_filter]}
            else:
                return {}
        
        for theater_name, theater_data in theaters_to_search.items():
            movies_on_date = []
            
            for movie in theater_data.get("movies", []):
                for schedule in movie.get("schedules", []):
                    if schedule.get("date") == target_date:
                        times = schedule.get("times", [])
                        
                        # 時間フィルタが指定されている場合
                        if time_filter:
                            filtered_times = self._filter_times_after(times, time_filter)
                            if not filtered_times:
                                continue
                            times = filtered_times
                        
                        movies_on_date.append({
                            "title": movie.get("title"),
                            "times": times,
                            "screen": schedule.get("screen", "")
                        })
            
            if movies_on_date:
                results[theater_name] = movies_on_date
        
        return results
    
    def _filter_times_after(self, times: List[str], after_time: str) -> List[str]:
        """指定時間以降の上映時間をフィルタ"""
        try:
            # "18:00"形式の時間を分に変換
            if ":" in after_time:
                hour, minute = map(int, after_time.split(":"))
                threshold_minutes = hour * 60 + minute
            else:
                # "18時"形式の場合
                hour = int(after_time.replace("時", ""))
                threshold_minutes = hour * 60
            
            filtered_times = []
            for time_str in times:
                try:
                    # "20:30"形式を分に変換
                    if ":" in time_str:
                        t_hour, t_minute = map(int, time_str.split(":"))
                        time_minutes = t_hour * 60 + t_minute
                        
                        if time_minutes >= threshold_minutes:
                            filtered_times.append(time_str)
                except:
                    # パースできない時間は除外
                    continue
            
            return filtered_times
        except:
            # エラーの場合は全て返す
            return times
    
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
                title = movie.get("title", "")
                # 部分一致検索
                if movie_name.lower() in title.lower() or title.lower() in movie_name.lower():
                    return {
                        "movie": movie,
                        "theater": theater_name,
                        "theater_data": theater_data
                    }
        return None


class ResponseFormatter:
    """応答テンプレート整形クラス"""
    
    @staticmethod
    def format_date_response(target_date: str, results: Dict[str, List[Dict]]) -> str:
        """日付検索結果を整形"""
        if not results:
            return f"{target_date}の上映予定は見つかりませんでした。"
        
        # 日付を読みやすい形式に変換
        try:
            date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%m月%d日(%a)').replace('Mon', '月').replace('Tue', '火').replace('Wed', '水').replace('Thu', '木').replace('Fri', '金').replace('Sat', '土').replace('Sun', '日')
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
        
        return response.strip()
    
    @staticmethod
    def format_theater_response(theater_data: Dict, theater_name: str) -> str:
        """劇場検索結果を整形"""
        # 映画館名にリンクを追加
        theater_url = theater_data.get('url', '')
        if theater_url and theater_url != '情報なし':
            response = f"■ [{theater_name}]({theater_url})\n"
        else:
            response = f"■ {theater_name}\n"
        
        response += f"・住所: {theater_data.get('address', '情報なし')}\n"
        if theater_url and theater_url != '情報なし':
            response += f"・URL: {theater_url}\n\n"
        else:
            response += "\n"
        
        movies = theater_data.get('movies', [])
        response += f"■ 上映中の映画（{len(movies)}本）\n\n"
        
        for movie in movies:
            title = movie.get('title', '不明')
            # 長いタイトルは短縮
            if len(title) > 40:
                title = title[:37] + "..."
            
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
        
        return response.strip()
    
    @staticmethod
    def format_movie_response(movie_info: Dict) -> str:
        """映画検索結果を整形"""
        movie = movie_info["movie"]
        theater = movie_info["theater"]
        
        response = f"■ 映画情報\n"
        response += f"・タイトル: {movie.get('title', '不明')}\n"
        response += f"・監督: {movie.get('director') or '情報なし'}\n"
        response += f"・出演: {', '.join(movie.get('cast', [])) or '情報なし'}\n"
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
        
        return response.strip()
    
    @staticmethod
    def format_no_match_response(query: str, keywords: Dict, method: str) -> str:
        """該当なしの場合の応答"""
        response = "申し訳ございませんが、お探しの情報が見つかりませんでした。\n\n"
        
        if keywords.get('dates'):
            response += f"検索した日付: {', '.join(keywords['dates'])}\n"
        if keywords.get('theaters'):
            response += f"検索した劇場: {', '.join(keywords['theaters'])}\n"
        if keywords.get('movies'):
            response += f"検索した映画: {', '.join(keywords['movies'])}\n"
        
        response += f"\n利用可能な検索:\n"
        response += f"・日付: 今日、明日、8月1日、この週末など\n"
        response += f"・劇場: ケイズシネマ、下高井戸シネマ、早稲田松竹、新宿武蔵野館\n"
        response += f"・映画: 「タイトル」で囲んで指定\n"
        
        return response


class HybridCinemaSystem:
    """完全なハイブリッド映画情報システム"""
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        """
        初期化
        
        Args:
            ollama_client: Ollamaクライアント
        """
        self.keyword_extractor = HybridKeywordExtractor(ollama_client)
        self.data_searcher = CinemaDataSearcher()
        self.formatter = ResponseFormatter()
    
    async def process_query(self, query: str) -> str:
        """
        クエリを処理して回答を生成
        
        Args:
            query: ユーザーの質問
            
        Returns:
            整形された回答文字列
        """
        print(f"DEBUG: 処理中のクエリ: {query}")
        
        # Step 1: キーワード抽出
        keywords, method = await self.keyword_extractor.extract_keywords(query)
        print(f"DEBUG: 抽出方法: {method}")
        print(f"DEBUG: 抽出結果: {keywords}")
        
        # Step 2: データ検索と回答生成（優先度順）
        
        # 映画検索を最優先
        if keywords.get('movies'):
            for movie_name in keywords['movies']:
                movie_info = self.data_searcher.search_movie_info(movie_name)
                if movie_info:
                    return self.formatter.format_movie_response(movie_info)
        
        # 日付+劇場+時間の複合検索
        if keywords.get('dates'):
            for target_date in keywords['dates']:
                theater_filter = keywords['theaters'][0] if keywords.get('theaters') else None
                time_filter = keywords['time_filters'][0] if keywords.get('time_filters') else None
                
                results = self.data_searcher.search_by_date(target_date, theater_filter, time_filter)
                if results:
                    # 複合検索の場合は詳細な説明を追加
                    if theater_filter or time_filter:
                        filter_desc = []
                        if theater_filter:
                            filter_desc.append(f"劇場: {theater_filter}")
                        if time_filter:
                            filter_desc.append(f"時間: {time_filter}以降")
                        filter_info = "（" + "、".join(filter_desc) + "）"
                        
                        response = self.formatter.format_date_response(target_date, results)
                        # タイトル行にフィルタ情報を追加
                        response = response.replace("の上映予定", f"の上映予定{filter_info}")
                        return response
                    else:
                        return self.formatter.format_date_response(target_date, results)
        
        # 劇場のみの検索
        if keywords.get('theaters'):
            for theater_name in keywords['theaters']:
                theater_data = self.data_searcher.search_theater_movies(theater_name)
                if theater_data:
                    return self.formatter.format_theater_response(theater_data, theater_name)
        
        # 該当なし
        return self.formatter.format_no_match_response(query, keywords, method)


# 統合テスト用関数
async def test_hybrid_cinema_system():
    """完全なハイブリッドシステムのテスト"""
    try:
        system = HybridCinemaSystem()
        
        test_queries = [
            "今日の映画は？",
            "明日ケイズシネマで何やってる？",
            "7月29日の上映予定は？",
            "「また逢いましょう」の上映時間は？",
            "ケイズシネマの映画教えて",
            "この週末に観られる映画は？",
            "存在しない映画について"
        ]
        
        print("=" * 70)
        print("完全ハイブリッドシステム - 統合テスト")
        print("=" * 70)
        
        for query in test_queries:
            print(f"\n【質問】: {query}")
            print("-" * 50)
            
            response = await system.process_query(query)
            print(response)
            print("-" * 50)
            
    except Exception as e:
        print(f"統合テストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_hybrid_cinema_system())