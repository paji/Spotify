#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.parse

# 設定
MP3_DIR = 'mp3_downloads'
PAGES_DIR = 'docs/podcast'
RSS_FILE = 'podcast.xml'
PAGES_RSS_FILE = 'docs/podcast.xml'
INDEX_FILE = 'docs/index.html'

# GitHubユーザー名とリポジトリ名（要変更）
github_username = 'paji'
repo_name = 'Spotify'

# GitHub PagesのベースURL
github_pages_url = f'https://{github_username}.github.io/{repo_name}/podcast'

def ensure_directory(directory):
    """ディレクトリが存在することを確認し、なければ作成"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"ディレクトリを作成しました: {directory}")

def copy_mp3_files():
    """MP3ファイルをGitHub Pagesディレクトリにコピー"""
    ensure_directory(PAGES_DIR)
    
    # MP3ファイルを取得
    mp3_files = []
    for file in os.listdir(MP3_DIR):
        if file.endswith('.mp3'):
            mp3_files.append(file)
    
    # コピー処理
    copied_count = 0
    for file in mp3_files:
        source = os.path.join(MP3_DIR, file)
        destination = os.path.join(PAGES_DIR, file)
        
        # ファイルが存在しないか、サイズが異なる場合にコピー
        if not os.path.exists(destination) or os.path.getsize(source) != os.path.getsize(destination):
            shutil.copy2(source, destination)
            copied_count += 1
            print(f"コピーしました: {file}")
    
    print(f"合計 {copied_count} 個のMP3ファイルをコピーしました")
    return mp3_files

def update_rss_for_github_pages():
    """RSSフィードをGitHub Pages用に更新"""
    if not os.path.exists(RSS_FILE):
        print(f"エラー: {RSS_FILE} が見つかりません")
        return False
    
    try:
        # XMLファイルを読み込む
        with open(RSS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 重複したXML宣言を削除
        content = re.sub(r'<\?xml.*?\?>\s*<\?xml.*?\?>', '<?xml version="1.0" encoding="UTF-8"?>', content)
        
        # 名前空間を登録
        ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
        ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
        
        # XMLを解析
        root = ET.fromstring(content)
        
        # すべてのenclosureとguidとlinkのURLをGitHub Pages用に変更
        for item in root.findall('.//item'):
            # ファイル名を取得
            for enclosure in item.findall('.//enclosure'):
                old_url = enclosure.get('url')
                filename = old_url.split('/')[-1]
                new_url = f"{github_pages_url}/{filename}"
                enclosure.set('url', new_url)
            
            for guid in item.findall('.//guid'):
                old_url = guid.text
                filename = old_url.split('/')[-1]
                new_url = f"{github_pages_url}/{filename}"
                guid.text = new_url
            
            for link in item.findall('.//link'):
                old_url = link.text
                filename = old_url.split('/')[-1]
                new_url = f"{github_pages_url}/{filename}"
                link.text = new_url
        
        # 更新したXMLを保存
        ensure_directory(os.path.dirname(PAGES_RSS_FILE))
        tree = ET.ElementTree(root)
        tree.write(PAGES_RSS_FILE, encoding='utf-8', xml_declaration=True)
        
        print(f"RSSフィードをGitHub Pages用に更新しました: {PAGES_RSS_FILE}")
        return True
    
    except Exception as e:
        print(f"RSSフィードの更新中にエラーが発生しました: {e}")
        return False

def create_index_html(mp3_files):
    """シンプルなindex.htmlを作成"""
    ensure_directory(os.path.dirname(INDEX_FILE))
    
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>裏・パジちゃんねる ポッドキャスト</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        ul {{
            list-style-type: none;
            padding: 0;
        }}
        li {{
            margin-bottom: 15px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .date {{
            color: #666;
            font-size: 0.9em;
        }}
        .rss-link {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 15px;
            background-color: #ff8800;
            color: white;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <h1>裏・パジちゃんねる ポッドキャスト</h1>
    <p>ブロックチェーンやAIなど最新テクノロジーについての考察を毎日配信</p>
    
    <a href="podcast.xml" class="rss-link">RSSフィードを購読</a>
    
    <h2>エピソード一覧</h2>
    <ul>
"""
    
    # MP3ファイルを日付順にソート（ファイル名の先頭が日付形式）
    mp3_files.sort(reverse=True)
    
    for file in mp3_files:
        # ファイル名から情報を抽出
        match = re.match(r'(\d{4}-\d{2}-\d{2})_(.+)_(\d+)\.mp3', file)
        if match:
            date_str, title, track_id = match.groups()
            # 引用符を削除
            title = title.replace('"', '')
            
            html_content += f"""        <li>
            <div class="date">{date_str}</div>
            <a href="podcast/{file}">{title}</a>
        </li>
"""
    
    html_content += """    </ul>
    
    <footer>
        <p>© 2025 パジ - 更新日時: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    </footer>
</body>
</html>
"""
    
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"index.htmlを作成しました: {INDEX_FILE}")

def main():
    """メイン処理"""
    print("GitHub Pages用のMP3ファイル更新を開始します...")
    
    # MP3ファイルをコピー
    mp3_files = copy_mp3_files()
    
    # RSSフィードを更新
    update_rss_for_github_pages()
    
    # index.htmlを作成
    create_index_html(mp3_files)
    
    print("GitHub Pages用の更新が完了しました")

if __name__ == "__main__":
    main()
