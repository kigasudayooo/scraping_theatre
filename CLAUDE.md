# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with this Japanese cinema web scraping and Discord bot project.

## Project Overview

A comprehensive system combining web scraping of Japanese cinema websites with Discord bot integration for automated notifications and interactive movie information queries. The project extracts structured movie data, schedules, and theater information, then provides weekly Discord notifications and on-demand movie searches.

**Key Features:**
- **Web Scraping**: Multi-theater HTML parsing with object-oriented architecture
- **Discord Integration**: Weekly notifications and interactive movie queries
- **Chat Bot**: General conversation bot with Ollama LLM integration
- **Data Management**: Structured data models with CSV export and Google Sheets integration
- **Scalable Architecture**: Abstract base classes for easy theater expansion
- **Japanese Text Support**: Proper encoding and formatting for Japanese content

## Development Guidelines

### Project Development Best Practices
- 開発は、必ずブランチを作成して、こまめにcommitするようにしてください。そのタイミングで、開発日誌への追記を行ってください。ある程度実装が進んだら、pushしてください。

## Discord Bot Architecture

### Bot Types
1. **Movie Bot** (`discord_bot_main.py`) - 映画館情報専用Bot
   - 週次通知機能
   - 映画検索機能
   - LLM応答機能（Ollama連携）

2. **Chat Bot** (`chat_bot.py`) - おしゃべり専用Bot
   - 一般的な会話機能
   - Ollama LLM連携
   - 会話履歴管理

### Bot Launcher
- **Multi Bot Launcher** (`multi_bot_launcher.py`) - 統合起動スクリプト
  ```bash
  # 映画館Bot起動
  python src/discord_bot/multi_bot_launcher.py --bot movie
  
  # チャットBot起動
  python src/discord_bot/multi_bot_launcher.py --bot chat
  
  # 単体起動も可能
  python src/discord_bot/chat_bot.py
  ```

### Technical Notes
- 同一Discordトークンでは複数Botの同時実行は不可
- 両Bot併用には別々のDiscordアプリ/トークンが必要

## Communication Guidelines

### Emoji Usage
- 絵文字を使用することを、あらゆる場面で禁止します。