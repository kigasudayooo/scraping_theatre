#!/usr/bin/env python3
"""
Discord Bot Log Viewer

View and analyze Discord bot conversation logs
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import argparse

def view_logs(log_file_path, show_details=False, filter_keyword=None):
    """View conversation logs"""
    
    log_file = Path(log_file_path)
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file_path}")
        return
    
    print(f"📁 Reading log file: {log_file.name}")
    print("=" * 60)
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    conversations = []
    for line in lines:
        try:
            conv = json.loads(line.strip())
            if filter_keyword:
                if filter_keyword.lower() in conv['user_message'].lower() or \
                   filter_keyword.lower() in conv['bot_response'].lower():
                    conversations.append(conv)
            else:
                conversations.append(conv)
        except json.JSONDecodeError:
            continue
    
    print(f"💬 Found {len(conversations)} conversations")
    
    if filter_keyword:
        print(f"🔍 Filtered by keyword: '{filter_keyword}'")
    
    print()
    
    for i, conv in enumerate(conversations, 1):
        timestamp = datetime.fromisoformat(conv['timestamp']).strftime("%H:%M:%S")
        user_msg = conv['user_message'][:50] + "..." if len(conv['user_message']) > 50 else conv['user_message']
        
        print(f"[{timestamp}] 👤 {user_msg}")
        
        if show_details:
            bot_response = conv['bot_response']
            if len(bot_response) > 200:
                bot_response = bot_response[:200] + "..."
            
            print(f"              🤖 {bot_response}")
            
            if 'metadata' in conv:
                metadata = conv['metadata']
                if 'user_name' in metadata:
                    print(f"              📝 User: {metadata['user_name']}")
                if 'response_length' in metadata:
                    print(f"              📏 Response length: {metadata['response_length']} chars")
                if 'channel_name' in metadata:
                    print(f"              📢 Channel: {metadata['channel_name']}")
        else:
            # Show just the first 100 chars of bot response
            bot_response = conv['bot_response'][:100] + "..." if len(conv['bot_response']) > 100 else conv['bot_response']
            print(f"              🤖 {bot_response}")
        
        print()

def analyze_logs(log_file_path):
    """Analyze conversation patterns"""
    
    log_file = Path(log_file_path)
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file_path}")
        return
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    conversations = []
    for line in lines:
        try:
            conv = json.loads(line.strip())
            conversations.append(conv)
        except json.JSONDecodeError:
            continue
    
    print(f"📊 Log Analysis for {log_file.name}")
    print("=" * 50)
    
    total_conversations = len(conversations)
    print(f"Total conversations: {total_conversations}")
    
    if total_conversations == 0:
        return
    
    # Response length analysis
    response_lengths = [len(conv['bot_response']) for conv in conversations]
    avg_response_length = sum(response_lengths) / len(response_lengths)
    print(f"Average response length: {avg_response_length:.1f} characters")
    
    # Common query patterns
    query_keywords = {}
    for conv in conversations:
        user_msg = conv['user_message'].lower()
        if 'について' in user_msg:
            query_keywords['movie_info'] = query_keywords.get('movie_info', 0) + 1
        elif '上映' in user_msg or 'スケジュール' in user_msg:
            query_keywords['schedule'] = query_keywords.get('schedule', 0) + 1
        elif '監督' in user_msg:
            query_keywords['director'] = query_keywords.get('director', 0) + 1
        else:
            query_keywords['other'] = query_keywords.get('other', 0) + 1
    
    print("\nQuery patterns:")
    for pattern, count in query_keywords.items():
        percentage = (count / total_conversations) * 100
        print(f"  {pattern}: {count} ({percentage:.1f}%)")
    
    # Look for potential hallucination indicators
    hallucination_indicators = 0
    for conv in conversations:
        response = conv['bot_response'].lower()
        # Simple heuristics for hallucination detection
        if any(indicator in response for indicator in [
            '監督:', '出演:', 'あらすじ:', '年に公開', '製作'
        ]) and 'information' not in response and '情報なし' not in response:
            hallucination_indicators += 1
    
    if hallucination_indicators > 0:
        hallucination_rate = (hallucination_indicators / total_conversations) * 100
        print(f"\n⚠️ Potential hallucination indicators: {hallucination_indicators} ({hallucination_rate:.1f}%)")

def main():
    parser = argparse.ArgumentParser(description='Discord Bot Log Viewer')
    parser.add_argument('--file', '-f', help='Log file path (default: latest log)')
    parser.add_argument('--details', '-d', action='store_true', help='Show detailed information')
    parser.add_argument('--filter', help='Filter by keyword')
    parser.add_argument('--analyze', '-a', action='store_true', help='Analyze log patterns')
    
    args = parser.parse_args()
    
    # Find log file
    if args.file:
        log_file_path = args.file
    else:
        logs_dir = Path("logs")
        if not logs_dir.exists():
            print("❌ No logs directory found")
            return 1
        
        log_files = list(logs_dir.glob("discord_conversations_*.jsonl"))
        if not log_files:
            print("❌ No conversation log files found")
            return 1
        
        # Use the most recent log file
        log_file_path = max(log_files, key=lambda f: f.stat().st_mtime)
    
    if args.analyze:
        analyze_logs(log_file_path)
    else:
        view_logs(log_file_path, args.details, args.filter)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())