#!/usr/bin/env python3
"""
キーワード検索ベースアプローチのプロトタイプ
LLMにデータ解析を依存せず、直接検索でハルシネーションを完全防止
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from difflib import SequenceMatcher

class KeywordSearchEngine:
    """キーワード検索ベースの映画情報抽出エンジン"""
    
    def __init__(self, data_file: str = "data/movies_data.json"):
        """
        初期化
        
        Args:
            data_file: 映画データJSONファイルのパス
        """
        self.data_file = Path(data_file)
        self.data = self._load_data()
        
        # キーワードパターン
        self.movie_patterns = [
            r'「(.+?)」',  # 「映画名」
            r'『(.+?)』',  # 『映画名』
            r'(.+?)について',  # 映画名について
            r'(.+?)の情報',  # 映画名の情報
        ]
        
        self.theater_patterns = [
            r'(.+?)(?:で|が|の).*(?:観られる|上映|映画)',  # ケイズシネマで観られる
            r'(.+?)(?:シネマ|映画館|劇場)',  # ケイズシネマ
        ]
        
        # 劇場名辞書（表記揺れ対応）
        self.theater_aliases = {
            'ケイズシネマ': ['ケイズ', 'kシネマ', 'ks cinema'],
            '下高井戸シネマ': ['下高井戸', 'シモタカ'],
            '早稲田松竹': ['早稲田', '松竹'],
            '新宿武蔵野館': ['武蔵野館', '新宿武蔵野', 'musashino']
        }
    
    def _load_data(self) -> Dict:
        """映画データを読み込み"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"データファイルが見つかりません: {self.data_file}")
            return {"theaters": {}}
    
    def extract_keywords(self, query: str) -> Tuple[List[str], List[str]]:
        """
        クエリからキーワードを抽出
        
        Args:
            query: ユーザーの質問
            
        Returns:
            Tuple[映画名候補リスト, 劇場名候補リスト]
        """
        movie_keywords = []
        theater_keywords = []
        
        # 映画名抽出
        for pattern in self.movie_patterns:
            matches = re.findall(pattern, query)
            movie_keywords.extend(matches)
        
        # 劇場名抽出
        for pattern in self.theater_patterns:
            matches = re.findall(pattern, query)
            theater_keywords.extend(matches)
        
        # 劇場名の正規化
        normalized_theaters = []
        for theater in theater_keywords:
            normalized = self._normalize_theater_name(theater)
            if normalized:
                normalized_theaters.append(normalized)
        
        return movie_keywords, normalized_theaters
    
    def _normalize_theater_name(self, name: str) -> Optional[str]:
        """劇場名を正規化"""
        name = name.strip()
        
        # 完全一致
        if name in self.theater_aliases:
            return name
        
        # エイリアス検索
        for official_name, aliases in self.theater_aliases.items():
            if name in aliases:
                return official_name
        
        # 部分一致（類似度ベース）
        for theater_name in self.theater_aliases.keys():
            similarity = SequenceMatcher(None, name.lower(), theater_name.lower()).ratio()
            if similarity > 0.6:  # 60%以上の類似度
                return theater_name
        
        return None
    
    def search_movie_info(self, movie_name: str) -> Optional[Dict]:
        """映画情報を検索"""
        for theater_name, theater_data in self.data.get("theaters", {}).items():
            for movie in theater_data.get("movies", []):
                if self._is_movie_match(movie.get("title", ""), movie_name):
                    return {
                        "movie": movie,
                        "theater": theater_name,
                        "theater_data": theater_data
                    }
        return None
    
    def search_theater_info(self, theater_name: str) -> Optional[Dict]:
        """劇場情報を検索"""
        theater_data = self.data.get("theaters", {}).get(theater_name)
        if theater_data:
            return theater_data
        return None
    
    def _is_movie_match(self, title: str, query: str) -> bool:
        """映画タイトルマッチング"""
        # 完全一致
        if title.lower() == query.lower():
            return True
        
        # 部分一致
        if query.lower() in title.lower() or title.lower() in query.lower():
            return True
        
        # 類似度ベース
        similarity = SequenceMatcher(None, title.lower(), query.lower()).ratio()
        return similarity > 0.7
    
    def format_movie_response(self, movie_info: Dict) -> str:
        """映画情報を固定テンプレートで整形"""
        movie = movie_info["movie"]
        theater = movie_info["theater"]
        
        response = f"■ 映画情報\n"
        response += f"- タイトル: {movie.get('title', '不明')}\n"
        response += f"- 監督: {movie.get('director') or '情報なし'}\n"
        response += f"- 出演: {', '.join(movie.get('cast', [])) or '情報なし'}\n"
        response += f"- ジャンル: {movie.get('genre') or '情報なし'}\n"
        response += f"- 上映時間: {movie.get('duration') or '情報なし'}\n"
        response += f"- あらすじ: {movie.get('synopsis') or '情報なし'}\n"
        
        response += f"\n■ 上映情報\n"
        response += f"- 劇場: {theater}\n"
        
        schedules = movie.get('schedules', [])
        if schedules:
            response += "- 上映スケジュール:\n"
            for schedule in schedules:
                date = schedule.get('date', '')
                times = ', '.join(schedule.get('times', []))
                screen = schedule.get('screen', '')
                response += f"  {date} {times}"
                if screen:
                    response += f" [{screen}]"
                response += "\n"
        else:
            response += "- 上映スケジュール: 情報なし\n"
        
        return response
    
    def format_theater_response(self, theater_data: Dict, theater_name: str) -> str:
        """劇場情報を固定テンプレートで整形"""
        response = f"■ 劇場情報\n"
        response += f"- 劇場名: {theater_name}\n"
        response += f"- 住所: {theater_data.get('address', '情報なし')}\n"
        response += f"- URL: {theater_data.get('url', '情報なし')}\n"
        
        movies = theater_data.get('movies', [])
        if movies:
            response += f"\n■ 上映中の映画（{len(movies)}本）\n"
            for i, movie in enumerate(movies, 1):
                title = movie.get('title', '不明')
                # 長いタイトルは短縮
                if len(title) > 30:
                    title = title[:27] + "..."
                response += f"{i}. {title}\n"
                
                schedules = movie.get('schedules', [])
                if schedules:
                    for schedule in schedules:
                        date = schedule.get('date', '')
                        times = ', '.join(schedule.get('times', []))
                        if date and times:
                            response += f"   {date} {times}\n"
        else:
            response += "\n■ 上映中の映画: 情報なし\n"
        
        return response
    
    def process_query(self, query: str) -> str:
        """
        クエリを処理して回答を生成
        
        Args:
            query: ユーザーの質問
            
        Returns:
            整形された回答文字列
        """
        movie_keywords, theater_keywords = self.extract_keywords(query)
        
        print(f"DEBUG: 抽出された映画キーワード: {movie_keywords}")
        print(f"DEBUG: 抽出された劇場キーワード: {theater_keywords}")
        
        # 映画情報検索を優先
        for movie_keyword in movie_keywords:
            movie_info = self.search_movie_info(movie_keyword)
            if movie_info:
                return self.format_movie_response(movie_info)
        
        # 劇場情報検索
        for theater_keyword in theater_keywords:
            theater_info = self.search_theater_info(theater_keyword)
            if theater_info:
                return self.format_theater_response(theater_info, theater_keyword)
        
        # 該当なしの場合
        return self._format_no_match_response(query, movie_keywords, theater_keywords)
    
    def _format_no_match_response(self, query: str, movies: List[str], theaters: List[str]) -> str:
        """該当なしの場合の応答"""
        response = "申し訳ございませんが、お探しの情報が見つかりませんでした。\n\n"
        
        if movies:
            response += f"検索した映画: {', '.join(movies)}\n"
        if theaters:
            response += f"検索した劇場: {', '.join(theaters)}\n"
        
        response += "\n対応している劇場:\n"
        for theater in self.theater_aliases.keys():
            response += f"- {theater}\n"
        
        response += "\n※映画タイトルは「」で囲むか、正確な名前で検索してください。"
        
        return response


def main():
    """テスト実行"""
    engine = KeywordSearchEngine()
    
    test_queries = [
        "「また逢いましょう」について教えて",
        "ケイズシネマで観られる映画は？",
        "下高井戸シネマの上映予定は？",
        "早稲田松竹ではどんな映画をやってる？",
        "存在しない映画について"
    ]
    
    print("=" * 60)
    print("キーワード検索ベースアプローチ - テスト実行")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n【質問】: {query}")
        print("-" * 40)
        response = engine.process_query(query)
        print(response)
        print("-" * 40)


if __name__ == "__main__":
    main()