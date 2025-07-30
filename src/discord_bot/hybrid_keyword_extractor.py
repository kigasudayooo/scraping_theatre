#!/usr/bin/env python3
"""
ハイブリッドキーワード抽出システム - 本格実装
LLMキーワード抽出 + プログラムデータ検索によるハルシネーション完全防止
"""

import json
import re
import sys
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# 既存のOllamaクライアントを使用
sys.path.insert(0, str(Path(__file__).parent))
from ollama_client import OllamaClient

class LLMKeywordExtractor:
    """LLMを使用したキーワード抽出器"""
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        """
        初期化
        
        Args:
            ollama_client: Ollamaクライアント（Noneの場合は新規作成）
        """
        self.ollama_client = ollama_client or OllamaClient()
        
        # キーワード抽出専用プロンプト（超厳格版）
        self.extraction_prompt = """
質問からキーワードを抽出してJSONで回答してください。

質問: {query}

重要: 質問に明確に含まれているキーワードのみ抽出してください。推測や創作は一切禁止です。

{{
  "dates": [],
  "theaters": [],
  "movies": [],
  "time_filters": []
}}

映画館名マッピング（略称→正式名称）:
- K's → ケイズシネマ
- ケイズ → ケイズシネマ  
- しもたか → 下高井戸シネマ
- 下高井戸 → 下高井戸シネマ
- 早稲田 → 早稲田松竹
- 松竹 → 早稲田松竹
- 武蔵野 → 新宿武蔵野館

日付マッピング:
- この週末 → [{weekend}]
- 今月末 → ["{month_end}"]
- 来週 → ["{next_week}"]
- 来週月曜日 → ["{next_monday}"]
- 来週火曜日 → ["{next_tuesday}"] 
- 来週水曜日 → ["{next_wednesday}"]
- 来週木曜日 → ["{next_thursday}"]
- 来週金曜日 → ["{next_friday}"]

時間フィルタ:
- 18時以降 → ["18:00"]
- 19時以降 → ["19:00"]
- 20時以降 → ["20:00"]
- 夜 → ["18:00"]
- 夕方以降 → ["17:00"]

映画名: 「」で囲まれたもののみ抽出

JSON形式のみで回答してください。
"""
    
    async def extract_keywords_with_llm(self, query: str) -> Dict[str, List[str]]:
        """
        LLMを使用してキーワードを抽出
        
        Args:
            query: ユーザーの質問
            
        Returns:
            抽出されたキーワード辞書
        """
        try:
            # 日付情報を生成
            today = date.today()
            tomorrow = today + timedelta(days=1)
            
            # 今週末（土日）を計算
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0:  # 今日が土曜日
                weekend_dates = [today, today + timedelta(days=1)]
            else:
                saturday = today + timedelta(days=days_until_saturday)
                weekend_dates = [saturday, saturday + timedelta(days=1)]
            
            # 今月末を計算
            next_month = today.replace(day=28) + timedelta(days=4)
            month_end = next_month - timedelta(days=next_month.day)
            
            # 来週の開始日を計算
            days_until_next_monday = (7 - today.weekday()) % 7
            if days_until_next_monday == 0:
                days_until_next_monday = 7
            next_week_start = today + timedelta(days=days_until_next_monday)
            
            # 来週の各曜日を計算
            next_monday = next_week_start
            next_tuesday = next_monday + timedelta(days=1)
            next_wednesday = next_monday + timedelta(days=2)
            next_thursday = next_monday + timedelta(days=3)
            next_friday = next_monday + timedelta(days=4)
            
            # プロンプトを生成
            weekend_str = f'"{weekend_dates[0].strftime("%Y-%m-%d")}", "{weekend_dates[1].strftime("%Y-%m-%d")}"'
            formatted_prompt = self.extraction_prompt.format(
                query=query,
                weekend=weekend_str,
                month_end=month_end.strftime('%Y-%m-%d'),
                next_week=next_week_start.strftime('%Y-%m-%d'),
                next_monday=next_monday.strftime('%Y-%m-%d'),
                next_tuesday=next_tuesday.strftime('%Y-%m-%d'),
                next_wednesday=next_wednesday.strftime('%Y-%m-%d'),
                next_thursday=next_thursday.strftime('%Y-%m-%d'),
                next_friday=next_friday.strftime('%Y-%m-%d')
            )
            
            # LLMに送信
            response = await self.ollama_client.generate_response(formatted_prompt)
            
            if not response or not response.content:
                return {'dates': [], 'theaters': [], 'movies': [], 'time_filters': []}
            
            # JSON解析を試行
            try:
                # LLMの回答からJSONを抽出
                response_text = response.content.strip()
                
                # JSONの開始/終了を探す
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    extracted = json.loads(json_text)
                    
                    # 結果を正規化
                    result = {
                        'dates': self._normalize_dates(extracted.get('dates', [])),
                        'theaters': self._normalize_theaters(extracted.get('theaters', [])),
                        'movies': extracted.get('movies', []),
                        'time_filters': extracted.get('time_filters', [])
                    }
                    
                    return result
                else:
                    print(f"DEBUG: JSON形式が見つかりません: {response_text}")
                    return {'dates': [], 'theaters': [], 'movies': [], 'time_filters': []}
                    
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON解析エラー: {e}, レスポンス: {response.content}")
                return {'dates': [], 'theaters': [], 'movies': [], 'time_filters': []}
            
        except Exception as e:
            print(f"DEBUG: LLM抽出エラー: {e}")
            return {'dates': [], 'theaters': [], 'movies': [], 'time_filters': []}
    
    def _normalize_dates(self, dates: List[str]) -> List[str]:
        """日付を正規化"""
        normalized = []
        for date_str in dates:
            # 既にYYYY-MM-DD形式かチェック
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                normalized.append(date_str)
            else:
                # その他の形式は無視（プログラム型に任せる）
                pass
        return normalized
    
    def _normalize_theaters(self, theaters: List[str]) -> List[str]:
        """劇場名を正規化"""
        theater_map = {
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
        
        normalized = []
        for theater in theaters:
            # 正式名称か確認
            official_theaters = ['ケイズシネマ', '下高井戸シネマ', '早稲田松竹', '新宿武蔵野館']
            if theater in official_theaters:
                normalized.append(theater)
            # エイリアス確認
            elif theater.lower() in [k.lower() for k in theater_map.keys()]:
                for alias, official in theater_map.items():
                    if theater.lower() == alias.lower():
                        normalized.append(official)
                        break
        
        return list(set(normalized))  # 重複除去


class ProgrammaticKeywordExtractor:
    """プログラム型キーワード抽出器（確実性重視）"""
    
    def __init__(self):
        self.date_patterns = {
            r'今日': 0,
            r'明日': 1,
            r'明後日': 2,
            r'昨日': -1,
            r'(\d{1,2})月(\d{1,2})日': 'specific_date',
            r'(\d{4})-(\d{1,2})-(\d{1,2})': 'iso_date',
            r'来週月曜日?': 'next_monday',
            r'来週火曜日?': 'next_tuesday',
            r'来週水曜日?': 'next_wednesday',
            r'来週木曜日?': 'next_thursday',
            r'来週金曜日?': 'next_friday',
            r'来週土曜日?': 'next_saturday',
            r'来週日曜日?': 'next_sunday'
        }
        
        self.theater_exact_patterns = [
            r'(ケイズシネマ|下高井戸シネマ|早稲田松竹|新宿武蔵野館)',
        ]
        
        self.movie_patterns = [
            r'「(.+?)」',
            r'『(.+?)』'
        ]
    
    def extract_keywords_programmatic(self, query: str) -> Dict[str, List[str]]:
        """プログラム型キーワード抽出"""
        result = {'dates': [], 'theaters': [], 'movies': [], 'time_filters': []}
        
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
            elif offset == 'iso_date':
                matches = re.findall(pattern, query)
                for year, month, day in matches:
                    try:
                        target_date = date(int(year), int(month), int(day))
                        result['dates'].append(target_date.strftime('%Y-%m-%d'))
                    except ValueError:
                        pass
            elif offset.startswith('next_'):
                if re.search(pattern, query):
                    # 来週の特定の曜日を計算
                    weekday_map = {
                        'next_monday': 0,
                        'next_tuesday': 1,
                        'next_wednesday': 2,
                        'next_thursday': 3,
                        'next_friday': 4,
                        'next_saturday': 5,
                        'next_sunday': 6
                    }
                    target_weekday = weekday_map[offset]
                    days_until_next_monday = (7 - today.weekday()) % 7
                    if days_until_next_monday == 0:
                        days_until_next_monday = 7
                    next_monday = today + timedelta(days=days_until_next_monday)
                    target_date = next_monday + timedelta(days=target_weekday)
                    result['dates'].append(target_date.strftime('%Y-%m-%d'))
        
        # 劇場抽出（厳密一致）
        for pattern in self.theater_exact_patterns:
            matches = re.findall(pattern, query)
            result['theaters'].extend(matches)
        
        # 映画抽出
        for pattern in self.movie_patterns:
            matches = re.findall(pattern, query)
            result['movies'].extend(matches)
        
        # 時間フィルタ抽出
        time_patterns = {
            r'(\d{1,2})時以降': lambda h: f"{h}:00",
            r'(\d{1,2}):(\d{2})以降': lambda h, m: f"{h}:{m}",
            r'夜': lambda: "18:00",
            r'夕方以降': lambda: "17:00"
        }
        
        for pattern, time_func in time_patterns.items():
            matches = re.findall(pattern, query)
            if matches:
                if pattern in [r'夜', r'夕方以降']:
                    result['time_filters'].append(time_func())
                else:
                    for match in matches:
                        if isinstance(match, tuple):
                            result['time_filters'].append(time_func(*match))
                        else:
                            result['time_filters'].append(time_func(match))
        
        return result


class HybridKeywordExtractor:
    """ハイブリッドキーワード抽出システム"""
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        """
        初期化
        
        Args:
            ollama_client: Ollamaクライアント
        """
        self.programmatic_extractor = ProgrammaticKeywordExtractor()
        self.llm_extractor = LLMKeywordExtractor(ollama_client)
    
    async def extract_keywords(self, query: str) -> Tuple[Dict[str, List[str]], str]:
        """
        段階的フォールバック方式でキーワード抽出
        
        Args:
            query: ユーザーの質問
            
        Returns:
            Tuple[抽出結果, 使用した方法]
        """
        print(f"DEBUG: キーワード抽出開始: {query}")
        
        # Step 1: プログラム型で試行
        prog_result = self.programmatic_extractor.extract_keywords_programmatic(query)
        prog_total = len(prog_result['dates']) + len(prog_result['theaters']) + len(prog_result['movies']) + len(prog_result.get('time_filters', []))
        
        print(f"DEBUG: プログラム型結果: {prog_result}, 合計: {prog_total}")
        
        # プログラム型で十分な結果が得られた場合
        if prog_total > 0:
            return prog_result, "programmatic"
        
        # Step 2: プログラム型で不十分な場合、LLM型を使用
        print("DEBUG: LLM型キーワード抽出を実行")
        llm_result = await self.llm_extractor.extract_keywords_with_llm(query)
        llm_total = len(llm_result['dates']) + len(llm_result['theaters']) + len(llm_result['movies']) + len(llm_result.get('time_filters', []))
        
        print(f"DEBUG: LLM型結果: {llm_result}, 合計: {llm_total}")
        
        if llm_total > 0:
            return llm_result, "llm_fallback"
        
        # Step 3: 両方とも失敗の場合
        return {'dates': [], 'theaters': [], 'movies': [], 'time_filters': []}, "failed"


# テスト用関数
async def test_hybrid_extractor():
    """ハイブリッド抽出器のテスト"""
    try:
        extractor = HybridKeywordExtractor()
        
        test_queries = [
            "今日の映画は？",
            "明日ケイズシネマで何やってる？",
            "この週末に観られる映画は？",
            "K'sの映画教えて",
            "しもたかで今月末に何かある？",
            "「また逢いましょう」の上映時間は？"
        ]
        
        print("=" * 60)
        print("ハイブリッドキーワード抽出器テスト")
        print("=" * 60)
        
        for query in test_queries:
            print(f"\n【質問】: {query}")
            print("-" * 40)
            
            keywords, method = await extractor.extract_keywords(query)
            
            print(f"使用手法: {method}")
            print(f"日付: {keywords['dates']}")
            print(f"劇場: {keywords['theaters']}")
            print(f"映画: {keywords['movies']}")
            
    except Exception as e:
        print(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_hybrid_extractor())