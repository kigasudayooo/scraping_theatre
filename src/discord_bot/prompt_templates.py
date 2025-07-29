"""
Prompt Templates for Ollama-powered Discord Bot

This module provides structured prompt templates for generating contextual responses
about cinema information, movie schedules, and related queries.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class PromptTemplate:
    """Base class for prompt templates"""
    
    def __init__(self, template: str, required_params: List[str] = None):
        """
        Initialize prompt template
        
        Args:
            template: Template string with {param} placeholders
            required_params: List of required parameter names
        """
        self.template = template
        self.required_params = required_params or []
    
    def format(self, **kwargs) -> str:
        """
        Format template with provided parameters
        
        Args:
            **kwargs: Template parameters
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValueError: If required parameters are missing
        """
        # Check for required parameters
        missing_params = [param for param in self.required_params if param not in kwargs]
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
        
        # Format template
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Template parameter not provided: {e}")

class CinemaPromptTemplates:
    """Collection of cinema-related prompt templates"""
    
    # Base system prompt for cinema assistant
    SYSTEM_BASE = PromptTemplate("""
あなたは東京の独立系映画館の案内をするAIアシスタントです。

【重要なルール】
1. 提供されたデータにない情報は絶対に創作・想像してはいけません
2. 監督名、出演者、あらすじなどが不明な場合は「情報なし」と明記してください
3. スケジュール情報は提供されたデータの通りに正確に記載してください
4. 分からないことは素直に「情報が見つかりません」と答えてください
5. 推測や一般知識での補完は行わないでください

対応映画館:
- ケイズシネマ (新宿)
- ポレポレ東中野  
- ユーロスペース (渋谷)
- 下高井戸シネマ
- 早稲田松竹 (高田馬場)
- 新宿武蔵野館

データ更新: {last_updated}
""")
    
    # Movie information query  
    MOVIE_INFO = PromptTemplate("""
映画「{movie_title}」の情報を以下のデータから回答してください。

提供データ:
{movie_data}

【厳格な回答ルール】
1. 上記データに記載された情報のみを使用してください
2. 監督・出演者・あらすじが空の場合は「情報なし」と記載
3. スケジュール情報は上記データの通りに正確に記載
4. 一般知識や推測での情報追加は禁止
5. データにない詳細は創作しないでください

回答形式:
- タイトル: [データ通り]
- 監督: [データにあれば記載、なければ「情報なし」]
- 出演: [データにあれば記載、なければ「情報なし」] 
- あらすじ: [データにあれば記載、なければ「情報なし」]
- 上映館: [データから]
- 上映スケジュール: [データ通りに正確に]

質問: {user_query}
""", required_params=["movie_title", "movie_data", "user_query"])
    
    # Theater schedule query
    THEATER_SCHEDULE = PromptTemplate("""
ユーザーから映画館「{theater_name}」のスケジュールについて質問されました。

以下の劇場データを参考に、上映スケジュールを正確に整理して説明してください:

{theater_data}

回答の重要なポイント:
1. 【今日以降の上映スケジュール】のみを表示してください
2. 各映画のタイトル、上映日時、スクリーン情報を正確に記載してください
3. 日付は「MM/DD(曜日)」形式で分かりやすく表示してください
4. 上映時間は提供されたデータ通りに記載してください
5. 映画館の基本情報（住所、公式サイト）も含めてください
6. スケジュール情報がない映画は「スケジュール未定」と明記してください

注意: 
- スケジュール情報は推測や創作をせず、提供されたデータのみを使用してください
- 過去の日付のスケジュールは表示しないでください

ユーザーの質問: {user_query}
""", required_params=["theater_name", "theater_data", "user_query"])
    
    # Director works query
    DIRECTOR_WORKS = PromptTemplate("""
ユーザーから監督「{director_name}」の作品について質問されました。

以下の映画データから該当する監督の作品を検索した結果:

{director_works}

回答のポイント:
- 該当する監督の作品一覧
- 各作品の上映情報
- 監督についての簡潔な説明（可能であれば）
- 上映スケジュールの詳細

ユーザーの質問: {user_query}
""", required_params=["director_name", "director_works", "user_query"])
    
    # General cinema query
    GENERAL_CINEMA = PromptTemplate("""
ユーザーから映画館に関する一般的な質問を受けました。

利用可能な映画館データ:
{cinema_data}

質問内容を分析して、最も適切な情報を提供してください。

回答のポイント:
- 質問の意図を理解する
- 関連する映画館や映画情報を提供
- おすすめがあれば提案する
- 具体的で実用的な情報を含める

ユーザーの質問: {user_query}
""", required_params=["cinema_data", "user_query"])
    
    # Help and introduction
    HELP_INFO = PromptTemplate("""
ユーザーがヘルプや使い方について質問しました。

以下の機能について説明してください:

利用可能な機能:
- 映画情報の検索: 「映画タイトル」について教えて
- 劇場スケジュール: 「劇場名」の上映予定は？
- 監督作品検索: 監督「監督名」の作品を教えて
- 一般的な映画相談

対応している映画館: {theater_count}館
最新データ更新: {last_updated}

回答のポイント:
- 分かりやすい使い方の説明
- 具体的な質問例を示す
- 親しみやすい口調で案内

ユーザーの質問: {user_query}
""", required_params=["theater_count", "last_updated", "user_query"])
    
    # Error fallback
    ERROR_FALLBACK = PromptTemplate("""
申し訳ございませんが、お探しの情報が見つかりませんでした。

検索対象: {search_target}
利用可能なデータ: {available_data}

以下のような方法で質問してみてください:
- 映画タイトルを正確に入力する
- 劇場名を正式名称で入力する
- 「おすすめの映画は？」のような一般的な質問

ユーザーの質問: {user_query}
""", required_params=["search_target", "available_data", "user_query"])

class PromptBuilder:
    """Helper class for building context-aware prompts"""
    
    def __init__(self, templates: CinemaPromptTemplates = None):
        """
        Initialize prompt builder
        
        Args:
            templates: Template collection to use
        """
        self.templates = templates or CinemaPromptTemplates()
    
    def build_system_prompt(self, last_updated: str = None) -> str:
        """
        Build base system prompt
        
        Args:
            last_updated: Data update timestamp
            
        Returns:
            Formatted system prompt
        """
        if not last_updated:
            last_updated = datetime.now().isoformat()
        
        return self.templates.SYSTEM_BASE.format(last_updated=last_updated)
    
    def build_movie_info_prompt(
        self, 
        movie_title: str, 
        movie_data: Dict[str, Any], 
        user_query: str
    ) -> str:
        """
        Build movie information prompt
        
        Args:
            movie_title: Movie title being queried
            movie_data: Relevant movie data
            user_query: Original user question
            
        Returns:
            Formatted prompt
        """
        # Format movie data for display
        formatted_data = self._format_movie_data(movie_data)
        
        return self.templates.MOVIE_INFO.format(
            movie_title=movie_title,
            movie_data=formatted_data,
            user_query=user_query
        )
    
    def build_theater_schedule_prompt(
        self,
        theater_name: str,
        theater_data: Dict[str, Any],
        user_query: str
    ) -> str:
        """
        Build theater schedule prompt
        
        Args:
            theater_name: Theater name being queried
            theater_data: Theater schedule data
            user_query: Original user question
            
        Returns:
            Formatted prompt
        """
        # Format theater data for display
        formatted_data = self._format_theater_data(theater_data)
        
        return self.templates.THEATER_SCHEDULE.format(
            theater_name=theater_name,
            theater_data=formatted_data,
            user_query=user_query
        )
    
    def build_director_works_prompt(
        self,
        director_name: str,
        director_works: List[Dict[str, Any]],
        user_query: str
    ) -> str:
        """
        Build director works prompt
        
        Args:
            director_name: Director name being queried
            director_works: List of director's movies
            user_query: Original user question
            
        Returns:
            Formatted prompt
        """
        # Format director works for display
        formatted_works = self._format_director_works(director_works)
        
        return self.templates.DIRECTOR_WORKS.format(
            director_name=director_name,
            director_works=formatted_works,
            user_query=user_query
        )
    
    def build_general_prompt(
        self,
        cinema_data: Dict[str, Any],
        user_query: str
    ) -> str:
        """
        Build general cinema query prompt
        
        Args:
            cinema_data: Complete cinema database
            user_query: User question
            
        Returns:
            Formatted prompt
        """
        # Format cinema data for display (summary)
        formatted_data = self._format_cinema_summary(cinema_data)
        
        return self.templates.GENERAL_CINEMA.format(
            cinema_data=formatted_data,
            user_query=user_query
        )
    
    def build_help_prompt(
        self,
        theater_count: int,
        last_updated: str,
        user_query: str
    ) -> str:
        """
        Build help information prompt
        
        Args:
            theater_count: Number of supported theaters
            last_updated: Last data update time
            user_query: User question
            
        Returns:
            Formatted prompt
        """
        return self.templates.HELP_INFO.format(
            theater_count=theater_count,
            last_updated=last_updated,
            user_query=user_query
        )
    
    def build_error_prompt(
        self,
        search_target: str,
        available_data: str,
        user_query: str
    ) -> str:
        """
        Build error fallback prompt
        
        Args:
            search_target: What user was searching for
            available_data: Brief description of available data
            user_query: Original user question
            
        Returns:
            Formatted prompt
        """
        return self.templates.ERROR_FALLBACK.format(
            search_target=search_target,
            available_data=available_data,
            user_query=user_query
        )
    
    def _format_movie_data(self, movie_data: Dict[str, Any]) -> str:
        """Format movie data for prompt inclusion"""
        if not movie_data:
            return "映画データが見つかりませんでした。"
        
        lines = []
        title = movie_data.get('title', '不明')
        lines.append(f"■ 映画情報: {title}")
        
        # 基本情報
        if movie_data.get('director'):
            lines.append(f"監督: {movie_data['director']}")
        
        if movie_data.get('cast') and movie_data['cast']:
            cast_list = movie_data['cast'][:3]  # First 3 cast members
            lines.append(f"出演: {', '.join(cast_list)}")
        
        if movie_data.get('genre'):
            lines.append(f"ジャンル: {movie_data['genre']}")
            
        if movie_data.get('duration'):
            lines.append(f"上映時間: {movie_data['duration']}")
        
        if movie_data.get('synopsis'):
            lines.append(f"あらすじ: {movie_data['synopsis']}")
        
        # 上映館情報
        theater_name = movie_data.get('theater_name', movie_data.get('theater_id', '不明'))
        lines.append(f"\n■ 上映館: {theater_name}")
        
        # スケジュール情報を詳細に表示
        if movie_data.get('schedules'):
            lines.append("\n■ 上映スケジュール:")
            from datetime import datetime, date
            today = date.today()
            
            # 有効なスケジュールのみを表示
            valid_schedules = [s for s in movie_data['schedules'] if s.get('date') and s.get('times')]
            
            if valid_schedules:
                for schedule in valid_schedules:
                    schedule_date = schedule.get('date', '')
                    times = schedule.get('times', [])
                    screen = schedule.get('screen', '')
                    
                    if schedule_date and times:
                        # 日付の解析
                        try:
                            schedule_date_obj = datetime.strptime(schedule_date, '%Y-%m-%d').date()
                            date_str = schedule_date_obj.strftime('%m/%d(%a)')
                            
                            # 今日以降のスケジュールのみ表示
                            if schedule_date_obj >= today:
                                screen_info = f" [{screen}]" if screen else ""
                                times_str = ', '.join(times)
                                lines.append(f"  {date_str}: {times_str}{screen_info}")
                        except ValueError:
                            # 日付解析エラーの場合は元の形式で表示
                            screen_info = f" [{screen}]" if screen else ""
                            times_str = ', '.join(times)
                            lines.append(f"  {schedule_date}: {times_str}{screen_info}")
            else:
                lines.append("  スケジュール情報が不完全です")
        else:
            lines.append("\n■ 上映スケジュール: 情報なし")
        
        return '\n'.join(lines)
    
    def _format_theater_data(self, theater_data: Dict[str, Any]) -> str:
        """Format theater data for prompt inclusion"""
        if not theater_data:
            return "劇場データが見つかりませんでした。"
        
        lines = []
        theater_name = theater_data.get('name', '不明')
        lines.append(f"■ 映画館情報: {theater_name}")
        
        if theater_data.get('address'):
            lines.append(f"住所: {theater_data['address']}")
        
        if theater_data.get('url'):
            lines.append(f"公式サイト: {theater_data['url']}")
        
        movies = theater_data.get('movies', [])
        
        # 有効な映画（スケジュールがあるもの）をフィルタリング
        from datetime import datetime, date
        today = date.today()
        
        movies_with_schedules = []
        movies_without_schedules = []
        
        for movie in movies:
            title = movie.get('title', '不明')
            schedules = movie.get('schedules', [])
            
            # タイトルが「■」で始まる場合はスキップ（メタ情報の可能性）
            if title.startswith('■'):
                continue
                
            # 有効なスケジュールがあるかチェック
            valid_schedules = []
            for schedule in schedules:
                schedule_date = schedule.get('date', '')
                times = schedule.get('times', [])
                if schedule_date and times:
                    try:
                        schedule_date_obj = datetime.strptime(schedule_date, '%Y-%m-%d').date()
                        if schedule_date_obj >= today:
                            valid_schedules.append(schedule)
                    except ValueError:
                        valid_schedules.append(schedule)  # 日付解析エラーでも含める
            
            if valid_schedules:
                movies_with_schedules.append((movie, valid_schedules))
            else:
                movies_without_schedules.append(movie)
        
        # スケジュールありの映画を表示
        if movies_with_schedules:
            lines.append(f"\n■ 現在上映中の映画 ({len(movies_with_schedules)}本):")
            for movie, valid_schedules in movies_with_schedules:
                title = movie.get('title', '不明')
                lines.append(f"\n【{title}】")
                
                # 監督情報があれば追加
                if movie.get('director'):
                    lines.append(f"  監督: {movie['director']}")
                
                # スケジュール詳細
                lines.append("  上映予定:")
                for schedule in valid_schedules[:5]:  # 最大5スケジュール
                    schedule_date = schedule.get('date', '')
                    times = schedule.get('times', [])
                    screen = schedule.get('screen', '')
                    
                    if schedule_date and times:
                        try:
                            schedule_date_obj = datetime.strptime(schedule_date, '%Y-%m-%d').date()
                            date_str = schedule_date_obj.strftime('%m/%d(%a)')
                        except ValueError:
                            date_str = schedule_date
                        
                        screen_info = f" [{screen}]" if screen else ""
                        times_str = ', '.join(times)
                        lines.append(f"    {date_str}: {times_str}{screen_info}")
        
        # スケジュールなしの映画も簡潔に表示
        if movies_without_schedules:
            lines.append(f"\n■ その他の映画情報 ({len(movies_without_schedules)}本):")
            for movie in movies_without_schedules[:3]:  # 最大3つまで
                title = movie.get('title', '不明')
                if not title.startswith('■'):  # メタ情報は除外
                    lines.append(f"  - {title}")
        
        return '\n'.join(lines)
    
    def _format_director_works(self, director_works: List[Dict[str, Any]]) -> str:
        """Format director works for prompt inclusion"""
        if not director_works:
            return "該当する監督の作品が見つかりませんでした。"
        
        lines = [f"見つかった作品数: {len(director_works)}本"]
        
        for work in director_works:
            title = work.get('title', '不明')
            theater = work.get('theater', '不明')
            schedules = work.get('schedules', [])
            
            work_line = f"- {title} ({theater})"
            if schedules:
                schedule_info = []
                for schedule in schedules[:1]:  # First schedule only
                    date = schedule.get('date', '')
                    times = schedule.get('times', [])
                    if date and times:
                        schedule_info.append(f"{date}: {', '.join(times[:2])}")
                if schedule_info:
                    work_line += f" - {schedule_info[0]}"
            
            lines.append(work_line)
        
        return '\n'.join(lines)
    
    def _format_cinema_summary(self, cinema_data: Dict[str, Any]) -> str:
        """Format cinema data summary for prompt inclusion"""
        if not cinema_data:
            return "映画館データが利用できません。"
        
        theaters = cinema_data.get('theaters', {})
        summary = cinema_data.get('summary', {})
        
        lines = []
        lines.append(f"対応映画館数: {len(theaters)}館")
        lines.append(f"総映画数: {summary.get('total_movies', 0)}本")
        
        if theaters:
            lines.append("\n各映画館の状況:")
            for theater_id, theater_data in theaters.items():
                name = theater_data.get('name', theater_id)
                movie_count = len(theater_data.get('movies', []))
                lines.append(f"- {name}: {movie_count}本上映中")
        
        return '\n'.join(lines)