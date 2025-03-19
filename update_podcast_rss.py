#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.parse
import html
import glob
import mutagen
from mutagen.mp3 import MP3
import shutil

# 設定
MP3_DIR = 'mp3_downloads'  # MP3ファイルのダウンロードディレクトリ
PAGES_DIR = 'docs/podcast'  # GitHub Pagesのディレクトリ
RSS_FILE = 'podcast.xml'  # 一時的なRSSファイルのパス
PAGES_RSS_FILE = 'docs/podcast.xml'  # GitHub Pagesに配置するRSSファイルのパス
INDEX_FILE = 'docs/index.html'  # インデックスページのパス
NOJEKYLL_FILE = 'docs/.nojekyll'  # GitHub Pages設定ファイル

# Podcastの情報
PODCAST_TITLE = "裏・パジちゃんねる"
PODCAST_DESCRIPTION = "ブロックチェーンやAI、最新テクノロジーについての考察を毎日配信"
PODCAST_LANGUAGE = "ja"
PODCAST_AUTHOR = "パジ"
PODCAST_EMAIL = "contact@example.com"  # 実際のメールアドレスに変更してください
PODCAST_IMAGE = "https://example.com/podcast-image.jpg"  # 実際の画像URLに変更してください
PODCAST_CATEGORY = "Technology"
PODCAST_EXPLICIT = "no"

# GitHubユーザー名とリポジトリ名
github_username = 'paji'
repo_name = 'Spotify'

# GitHub PagesのベースURL（重要：正しいパスであることを確認）
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

def get_mp3_files():
    """MP3ファイルの情報を取得する"""
    mp3_files = []
    
    # MP3ディレクトリが存在するか確認
    if not os.path.exists(MP3_DIR):
        print(f"エラー: {MP3_DIR} ディレクトリが見つかりません")
        return mp3_files
    
    # MP3ファイルを検索して情報を収集
    for mp3_file in glob.glob(os.path.join(MP3_DIR, "*.mp3")):
        filename = os.path.basename(mp3_file)
        
        try:
            # MP3ファイルのメタデータを取得
            audio = MP3(mp3_file)
            
            # ファイルサイズを取得
            file_size = os.path.getsize(mp3_file)
            
            # ファイル名から情報を抽出（日付_タイトル_トラックID.mp3の形式を想定）
            match = re.match(r'(\d{4}-\d{2}-\d{2})_(.+)_(\d+)\.mp3', filename)
            
            if match:
                date_str, title, track_id = match.groups()
                # 日付文字列をDatetime形式に変換
                pub_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # 引用符を削除
                title = title.replace('"', '')
            else:
                # ファイル名から情報が抽出できない場合
                title = os.path.splitext(filename)[0]
                pub_date = datetime.fromtimestamp(os.path.getctime(mp3_file))
            
            # 情報を辞書にまとめる
            mp3_info = {
                'filename': filename,
                'title': title,
                'pub_date': pub_date,
                'file_size': file_size,
                'duration': int(audio.info.length),  # 秒単位の再生時間
                'full_path': mp3_file
            }
            
            mp3_files.append(mp3_info)
            
        except Exception as e:
            print(f"MP3ファイルの処理中にエラーが発生しました: {filename} - {e}")
    
    # 公開日時で降順ソート（新しい順）
    mp3_files.sort(key=lambda x: x['pub_date'], reverse=True)
    
    return mp3_files

def format_rfc822_date(dt):
    """日時をRFC822形式（Podcastで使用される形式）に変換"""
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    weekday = weekdays[dt.weekday()]
    month = months[dt.month - 1]
    
    return f"{weekday}, {dt.day:02d} {month} {dt.year} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} +0900"

def create_rss_feed(mp3_files):
    """RSSフィードを作成"""
    # RSSルート要素を作成
    rss = ET.Element('rss', {
        'version': '2.0',
        'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        'xmlns:content': 'http://purl.org/rss/1.0/modules/content/'
    })
    
    # チャンネル要素を作成
    channel = ET.SubElement(rss, 'channel')
    
    # チャンネル基本情報
    ET.SubElement(channel, 'title').text = PODCAST_TITLE
    ET.SubElement(channel, 'description').text = PODCAST_DESCRIPTION
    ET.SubElement(channel, 'language').text = PODCAST_LANGUAGE
    ET.SubElement(channel, 'link').text = github_pages_url
    ET.SubElement(channel, 'lastBuildDate').text = format_rfc822_date(datetime.now())
    
    # iTunes情報
    ET.SubElement(channel, 'itunes:author').text = PODCAST_AUTHOR
    ET.SubElement(channel, 'itunes:explicit').text = PODCAST_EXPLICIT
    
    # iTunes所有者情報
    owner = ET.SubElement(channel, 'itunes:owner')
    ET.SubElement(owner, 'itunes:name').text = PODCAST_AUTHOR
    ET.SubElement(owner, 'itunes:email').text = PODCAST_EMAIL
    
    # iTunesカテゴリ
    category = ET.SubElement(channel, 'itunes:category', {'text': PODCAST_CATEGORY})
    
    # iTunesイメージ
    ET.SubElement(channel, 'itunes:image', {'href': PODCAST_IMAGE})
    
    # 通常のイメージ
    image = ET.SubElement(channel, 'image')
    ET.SubElement(image, 'url').text = PODCAST_IMAGE
    ET.SubElement(image, 'title').text = PODCAST_TITLE
    ET.SubElement(image, 'link').text = github_pages_url
    
    # エピソードを追加
    for mp3_info in mp3_files:
        # ファイル名をURLエンコード（重要！）
        encoded_filename = urllib.parse.quote(mp3_info['filename'])
        file_url = f"{github_pages_url}/{encoded_filename}"
        
        # item要素を作成
        item = ET.SubElement(channel, 'item')
        
        # 基本情報（タイトルはhtml.escapeでエスケープ）
        title_text = html.escape(mp3_info['title'])
        ET.SubElement(item, 'title').text = title_text
        ET.SubElement(item, 'description').text = title_text
        ET.SubElement(item, 'pubDate').text = format_rfc822_date(mp3_info['pub_date'])
        
        # guid（一意のID）
        guid = ET.SubElement(item, 'guid', {'isPermaLink': 'true'})
        guid.text = file_url
        
        # enclosure（ファイル情報）
        ET.SubElement(item, 'enclosure', {
            'url': file_url,
            'type': 'audio/mpeg',
            'length': str(mp3_info['file_size'])
        })
        
        # リンク
        ET.SubElement(item, 'link').text = file_url
        
        # iTunes情報
        ET.SubElement(item, 'itunes:duration').text = str(mp3_info['duration'])
        ET.SubElement(item, 'itunes:author').text = PODCAST_AUTHOR
        ET.SubElement(item, 'itunes:explicit').text = PODCAST_EXPLICIT
    
    # XML宣言を明示的に指定
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    
    # XMLをテキストに変換（encoding='unicode'で文字化けを防止）
    xml_string = ET.tostring(rss, encoding='unicode', method='xml')
    
    # 一時的なRSSファイルに保存
    with open(RSS_FILE, 'w', encoding='utf-8') as f:
        f.write(xml_declaration)
        f.write(xml_string)
    
    # GitHub Pages用のRSSファイルにコピー
    ensure_directory(os.path.dirname(PAGES_RSS_FILE))
    with open(PAGES_RSS_FILE, 'w', encoding='utf-8') as f:
        f.write(xml_declaration)
        f.write(xml_string)
    
    print(f"RSSフィードを作成しました: {RSS_FILE}")
    print(f"GitHub Pages用RSSフィードをコピーしました: {PAGES_RSS_FILE}")

def create_index_html(mp3_files):
    """シンプルなindex.htmlを作成"""
    ensure_directory(os.path.dirname(INDEX_FILE))
    
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>裏・パジちゃんねる ポッドキャスト</title>
    <style>
        body {{
            font-family: Arial, 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', Meiryo, sans-serif;
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
    <p>ブロックチェーンやAI、最新テクノロジーについての考察を毎日配信</p>
    
    <a href="podcast.xml" class="rss-link">RSSフィードを購読</a>
    
    <h2>エピソード一覧</h2>
    <ul>
"""
    
    # MP3ファイルを日付順にソート（ファイル名の先頭が日付形式）
    mp3_files.sort(key=lambda x: x['pub_date'], reverse=True)
    
    for mp3_info in mp3_files:
        # タイトルを適切にHTMLエスケープして表示
        title_display = html.escape(mp3_info['title'])
        # ファイル名をURLエンコード
        file_encoded = urllib.parse.quote(mp3_info['filename'])
        # 日付を表示用にフォーマット
        display_date = mp3_info['pub_date'].strftime('%Y-%m-%d')
        
        html_content += f"""        <li>
            <div class="date">{display_date}</div>
            <a href="podcast/{file_encoded}">{title_display}</a>
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

def create_nojekyll_file():
    """GitHub Pagesで.nojekyllファイルを作成"""
    with open(NOJEKYLL_FILE, 'w') as f:
        pass
    print(f".nojekyllファイルを作成しました: {NOJEKYLL_FILE}")

def main():
    """メイン処理"""
    print("GitHub Pages用のMP3ファイル更新を開始します...")
    
    # MP3ファイルをコピー
    copy_mp3_files()
    
    # MP3ファイルの情報を取得
    mp3_files = get_mp3_files()
    
    if not mp3_files:
        print("警告: 処理するMP3ファイルがありませんでした")
        return
    
    print(f"{len(mp3_files)}個のMP3ファイルを処理します")
    
    # RSSフィードを作成
    create_rss_feed(mp3_files)
    
    # index.htmlを作成
    create_index_html(mp3_files)
    
    # .nojekyllファイルを作成
    create_nojekyll_file()
    
    print("GitHub Pages用の更新が完了しました")

if __name__ == "__main__":
    main()
