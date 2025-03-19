#!/usr/bin/env python3
"""
MP3ポッドキャストファイルを自動監視し、Spotify用のRSSフィードを生成するスクリプト
GitHub Actionsで毎時間実行されます
"""

import os
import glob
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from datetime import datetime
import re
import mutagen
from mutagen.mp3 import MP3

# 定数
MP3_DIR = "mp3_downloads"
RSS_FILE = "podcast.xml"
GITHUB_REPO_URL = "https://github.com/paji/Spotify"
RAW_GITHUB_URL = "https://raw.githubusercontent.com/paji/Spotify/main"

def get_mp3_files():
    """MP3ファイルの一覧を取得"""
    mp3_files = glob.glob(f"{MP3_DIR}/*.mp3")
    # 日付の新しい順にソート（ファイル名の先頭が日付形式）
    mp3_files.sort(reverse=True)
    return mp3_files

def get_mp3_info(file_path):
    """MP3ファイルの情報を取得"""
    try:
        audio = MP3(file_path)
        
        # ファイル名からタイトルを抽出
        filename = os.path.basename(file_path)
        # 日付とタイトルを分離（例: 2025-03-19_タイトル_ID.mp3）
        match = re.match(r'(\d{4}-\d{2}-\d{2})_(.+)_(\d+)\.mp3', filename)
        
        if match:
            date_str, title, track_id = match.groups()
            # 日付をRFC822形式に変換
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            pub_date = date_obj.strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # ファイルサイズを取得
            file_size = os.path.getsize(file_path)
            
            # 再生時間を取得（秒）
            duration_seconds = int(audio.info.length)
            hours, remainder = divmod(duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            return {
                'title': title,
                'pub_date': pub_date,
                'file_size': file_size,
                'duration': duration,
                'file_name': filename,
                'track_id': track_id
            }
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return None

def update_rss_feed():
    """RSSフィードを更新"""
    try:
        # 既存のRSSファイルを読み込む
        tree = ET.parse(RSS_FILE)
        root = tree.getroot()
        channel = root.find('channel')
        
        # 既存のitemを削除
        for item in channel.findall('item'):
            channel.remove(item)
        
        # MP3ファイルの情報を取得
        mp3_files = get_mp3_files()
        
        # 各MP3ファイルに対してitemを作成
        for mp3_file in mp3_files:
            info = get_mp3_info(mp3_file)
            if info:
                # 新しいitemエレメントを作成
                item = ET.SubElement(channel, 'item')
                
                # タイトル
                title = ET.SubElement(item, 'title')
                title.text = info['title']
                
                # 説明
                description = ET.SubElement(item, 'description')
                description.text = f"{info['title']} - ブロックチェーンやAIなど最新テクノロジーについての考察を毎日配信、濃密情報はプレミアムへ→ https://voicy.jp/channel/2834/all?premium=1 パジの日々の挑戦を記録していきます"
                
                # リンク
                link = ET.SubElement(item, 'link')
                link.text = f"{RAW_GITHUB_URL}/{MP3_DIR}/{info['file_name']}"
                
                # 公開日
                pub_date = ET.SubElement(item, 'pubDate')
                pub_date.text = info['pub_date']
                
                # GUID
                guid = ET.SubElement(item, 'guid')
                guid.set('isPermaLink', 'false')
                guid.text = f"{RAW_GITHUB_URL}/{MP3_DIR}/{info['file_name']}"
                
                # エンクロージャ
                enclosure = ET.SubElement(item, 'enclosure')
                enclosure.set('url', f"{RAW_GITHUB_URL}/{MP3_DIR}/{info['file_name']}")
                enclosure.set('length', str(info['file_size']))
                enclosure.set('type', 'audio/mpeg')
                
                # iTunes関連の情報
                itunes_duration = ET.SubElement(item, 'itunes:duration')
                itunes_duration.text = info['duration']
                
                itunes_explicit = ET.SubElement(item, 'itunes:explicit')
                itunes_explicit.text = 'no'
                
                itunes_author = ET.SubElement(item, 'itunes:author')
                itunes_author.text = 'パジ'
        
        # XMLを整形して保存
        xml_str = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
        
        # XML宣言を修正（minidomが追加する余分な行を削除）
        pretty_xml = re.sub(r'<\?xml version="1.0" \?>\n', '', pretty_xml)
        pretty_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml
        
        with open(RSS_FILE, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        print(f"RSSフィードを更新しました: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"処理したMP3ファイル数: {len(mp3_files)}")
        
    except Exception as e:
        print(f"RSSフィードの更新中にエラーが発生しました: {e}")

if __name__ == "__main__":
    update_rss_feed()
