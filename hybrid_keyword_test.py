#!/usr/bin/env python3
"""
ハイブリッドアプローチのテスト
LLMでキーワード抽出 → プログラムでデータ検索
"""

import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional

class HybridKeywordExtractor:
    """ハイブリッド型キーワード抽出器"""
    
    def __init__(self):
        # プログラム型パターン（確実）
        self.date_patterns = {
            r'今日': 0,
            r'明日': 1, 
            r'明後日': 2,
            r'昨日': -1,
            r'(\d{1,2})月(\d{1,2})日': 'specific_date',
            r'(\d{4})-(\d{1,2})-(\d{1,2})': 'iso_date'
        }
        
        self.theater_patterns = [
            r'(ケイズシネマ|下高井戸シネマ|早稲田松竹|新宿武蔵野館)',
            r'(.+?)(?:で|が|の).*(?:観られる|上映|映画)',
        ]
        
        self.movie_patterns = [
            r'「(.+?)」',
            r'『(.+?)』', 
            r'(.+?)について',
        ]
    
    def extract_keywords_programmatic(self, query: str) -> Dict[str, any]:
        """プログラム型キーワード抽出（確実だが限定的）"""
        result = {
            'dates': [],
            'theaters': [],
            'movies': [],
            'method': 'programmatic'
        }
        
        # 日付抽出
        today = date.today()
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
        
        # 劇場抽出
        for pattern in self.theater_patterns:
            matches = re.findall(pattern, query)
            result['theaters'].extend(matches)
        
        # 映画抽出  
        for pattern in self.movie_patterns:
            matches = re.findall(pattern, query)
            result['movies'].extend(matches)
        
        return result
    
    def extract_keywords_llm_simulation(self, query: str) -> Dict[str, any]:
        """LLM型キーワード抽出のシミュレーション"""
        # 実際のLLMを呼ぶ代わりに、期待される動作をシミュレート
        result = {
            'dates': [],
            'theaters': [],
            'movies': [],
            'method': 'llm_simulation'
        }
        
        # LLMが理解できそうな複雑なパターン
        llm_patterns = {
            'この週末': ['2025-08-02', '2025-08-03'],  # 土日
            '来週の月曜': ['2025-08-04'],
            '8月最初の週': ['2025-08-01', '2025-08-02', '2025-08-03'],
            '今月末': ['2025-07-31'],
            'お盆期間': ['2025-08-15', '2025-08-16'],
        }
        
        # LLMが理解できそうな劇場表現
        theater_aliases = {
            'K\'s': 'ケイズシネマ',
            'ケイズ': 'ケイズシネマ',
            '下高井戸': '下高井戸シネマ',
            'しもたか': '下高井戸シネマ',
            '早稲田': '早稲田松竹',
            '松竹': '早稲田松竹',
            '武蔵野': '新宿武蔵野館',
            '新宿の映画館': '新宿武蔵野館'
        }
        
        # LLMシミュレーション処理
        query_lower = query.lower()
        
        for pattern, dates in llm_patterns.items():
            if pattern in query:
                result['dates'].extend(dates)
        
        for alias, official in theater_aliases.items():
            if alias in query:
                result['theaters'].append(official)
        
        # 基本的な映画名抽出はプログラム型と同じ
        for pattern in self.movie_patterns:
            matches = re.findall(pattern, query)
            result['movies'].extend(matches)
        
        return result
    
    def compare_approaches(self, query: str) -> Dict:
        """両アプローチの比較"""
        prog_result = self.extract_keywords_programmatic(query)
        llm_result = self.extract_keywords_llm_simulation(query)
        
        return {
            'query': query,
            'programmatic': prog_result,
            'llm_simulation': llm_result,
            'recommendation': self._recommend_approach(prog_result, llm_result)
        }
    
    def _recommend_approach(self, prog: Dict, llm: Dict) -> str:
        """どちらのアプローチが良いかを判定"""
        prog_total = len(prog['dates']) + len(prog['theaters']) + len(prog['movies'])
        llm_total = len(llm['dates']) + len(llm['theaters']) + len(llm['movies'])
        
        if prog_total > 0 and llm_total == 0:
            return "プログラム型で十分（確実性重視）"
        elif prog_total == 0 and llm_total > 0:
            return "LLM型が必要（理解力重視）"
        elif prog_total > 0 and llm_total > 0:
            return "両方有効（LLM型がより多くを理解）"
        else:
            return "両方とも抽出失敗"


def main():
    """テスト実行"""
    extractor = HybridKeywordExtractor()
    
    test_queries = [
        "今日の映画は？",
        "明日ケイズシネマで何やってる？",
        "この週末に観られる映画は？",
        "下高井戸で8月1日の上映予定は？",
        "K'sシネマの来週の予定教えて",
        "しもたかで今月末に何かある？",
        "「また逢いましょう」の上映時間は？",
        "早稲田の映画館でお盆期間の映画は？"
    ]
    
    print("=" * 70)
    print("ハイブリッドアプローチ比較テスト")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\n【質問】: {query}")
        print("-" * 50)
        
        result = extractor.compare_approaches(query)
        
        print(f"📋 プログラム型結果:")
        prog = result['programmatic']
        print(f"  日付: {prog['dates']}")
        print(f"  劇場: {prog['theaters']}")  
        print(f"  映画: {prog['movies']}")
        
        print(f"🤖 LLM型結果（シミュレーション）:")
        llm = result['llm_simulation']
        print(f"  日付: {llm['dates']}")
        print(f"  劇場: {llm['theaters']}")
        print(f"  映画: {llm['movies']}")
        
        print(f"💡 推奨: {result['recommendation']}")


if __name__ == "__main__":
    main()