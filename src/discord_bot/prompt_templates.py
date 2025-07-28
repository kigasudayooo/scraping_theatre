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
あなたは東京の独立系映画館の案内をする親切なAIアシスタントです。

あなたの特徴:
- 映画と映画館に関する豊富な知識を持っています
- 日本語で自然な会話ができます
- ユーザーの質問に対して正確で役立つ情報を提供します
- 分からないことがあれば素直に「分からない」と答えます

現在対応している映画館:
- ケイズシネマ (新宿)
- ポレポレ東中野
- ユーロスペース (渋谷)
- 下高井戸シネマ
- 早稲田松竹 (高田馬場)
- 新宿武蔵野館

最新情報の更新日時: {last_updated}
""")
    
    # Movie information query
    MOVIE_INFO = PromptTemplate("""
ユーザーから映画「{movie_title}」について質問されました。

以下の映画データを参考に、この映画について詳しく説明してください:

{movie_data}

回答のポイント:
- 映画の基本情報（監督、出演者、あらすじなど）
- 上映スケジュールと劇場情報
- 特別な上映情報やイベント情報があれば含める
- 情報が不足している場合は、利用可能な情報のみを提供

ユーザーの質問: {user_query}
""", required_params=["movie_title", "movie_data", "user_query"])
    
    # Theater schedule query
    THEATER_SCHEDULE = PromptTemplate("""
ユーザーから映画館「{theater_name}」のスケジュールについて質問されました。

以下の劇場データを参考に、上映スケジュールを分かりやすく説明してください:

{theater_data}

回答のポイント:
- 現在上映中の映画一覧
- 各映画の上映時間と日程
- アクセス情報や連絡先があれば含める
- 見やすい形式でスケジュールを整理

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
        lines.append(f"タイトル: {title}")
        
        if movie_data.get('director'):
            lines.append(f"監督: {movie_data['director']}")
        
        if movie_data.get('cast'):
            cast_list = movie_data['cast'][:3]  # First 3 cast members
            lines.append(f"出演: {', '.join(cast_list)}")
        
        if movie_data.get('synopsis'):
            lines.append(f"あらすじ: {movie_data['synopsis']}")
        
        if movie_data.get('schedules'):
            lines.append("上映スケジュール:")
            for schedule in movie_data['schedules']:
                date = schedule.get('date', '')
                times = schedule.get('times', [])
                if date and times:
                    lines.append(f"  {date}: {', '.join(times)}")
        
        return '\n'.join(lines)
    
    def _format_theater_data(self, theater_data: Dict[str, Any]) -> str:
        """Format theater data for prompt inclusion"""
        if not theater_data:
            return "劇場データが見つかりませんでした。"
        
        lines = []
        theater_name = theater_data.get('name', '不明')
        lines.append(f"劇場名: {theater_name}")
        
        if theater_data.get('address'):
            lines.append(f"住所: {theater_data['address']}")
        
        movies = theater_data.get('movies', [])
        if movies:
            lines.append(f"\n現在上映中の映画 ({len(movies)}本):")
            for movie in movies:
                title = movie.get('title', '不明')
                schedules = movie.get('schedules', [])
                
                movie_line = f"- {title}"
                if schedules:
                    schedule_summary = []
                    for schedule in schedules[:2]:  # First 2 schedules
                        date = schedule.get('date', '')
                        times = schedule.get('times', [])
                        if date and times:
                            schedule_summary.append(f"{date}: {', '.join(times)}")
                    if schedule_summary:
                        movie_line += f" ({'; '.join(schedule_summary)})"
                
                lines.append(movie_line)
        
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