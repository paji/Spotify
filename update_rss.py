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
import urllib.parse
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
            # ファイルサイズが0の場合はデフォルト値を設定（2MB = 2097152バイト）
            if file_size == 0:
                file_size = 2097152
            
            # 再生時間を取得（秒）- MP3メタデータが読めない場合はデフォルト値を使用
            duration = "00:30:00"  # デフォルト30分
            try:
                audio = MP3(file_path)
                duration_seconds = int(audio.info.length)
                hours, remainder = divmod(duration_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            except Exception as e:
                print(f"MP3メタデータ読み取りエラー（デフォルト時間を使用）: {e}")
            
            # ファイル名から引用符を削除
            clean_filename = filename.replace('"', '')
            
            return {
                'title': title,
                'pub_date': pub_date,
                'file_size': file_size,
                'duration': duration,
                'file_name': clean_filename,
                'original_filename': filename,
                'track_id': track_id
            }
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return None

def create_new_rss_feed():
    """新規RSSフィードを作成"""
    # 名前空間を登録
    ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
    
    # ルート要素を作成
    rss = ET.Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
    
    # チャンネル要素を作成
    channel = ET.SubElement(rss, 'channel')
    
    # チャンネル情報を設定
    title = ET.SubElement(channel, 'title')
    title.text = 'パジのテック雑談'
    
    link = ET.SubElement(channel, 'link')
    link.text = GITHUB_REPO_URL
    
    description = ET.SubElement(channel, 'description')
    description.text = 'ブロックチェーンやAIなど最新テクノロジーについての考察を毎日配信、濃密情報はプレミアムへ→ https://voicy.jp/channel/2834/all?premium=1 パジの日々の挑戦を記録していきます'
    
    language = ET.SubElement(channel, 'language')
    language.text = 'ja-jp'
    
    copyright = ET.SubElement(channel, 'copyright')
    copyright.text = f'Copyright {datetime.now().year} パジ'
    
    lastBuildDate = ET.SubElement(channel, 'lastBuildDate')
    lastBuildDate.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    # iTunes固有の情報
    itunes_author = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}author')
    itunes_author.text = 'パジ'
    
    itunes_subtitle = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}subtitle')
    itunes_subtitle.text = 'テクノロジーと日常の考察'
    
    itunes_summary = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}summary')
    itunes_summary.text = 'ブロックチェーンやAIなど最新テクノロジーについての考察を毎日配信、濃密情報はプレミアムへ→ https://voicy.jp/channel/2834/all?premium=1 パジの日々の挑戦を記録していきます'
    
    itunes_explicit = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit')
    itunes_explicit.text = 'no'
    
    # カテゴリ
    itunes_category = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}category')
    itunes_category.set('text', 'Technology')
    
    # イメージ
    itunes_image = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}image')
    itunes_image.set('href', f'{RAW_GITHUB_URL}/podcast_cover.jpg')
    
    # XMLを整形して保存
    xml_str = ET.tostring(rss, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    # XML宣言を修正
    pretty_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml.split('\n', 1)[1]
    
    with open(RSS_FILE, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)

def update_rss_feed():
    """RSSフィードを更新"""
    try:
        # MP3ディレクトリが存在しない場合は作成
        if not os.path.exists(MP3_DIR):
            os.makedirs(MP3_DIR)
            print(f"{MP3_DIR}ディレクトリを作成しました")
        
        # RSSファイルが存在しない場合は新規作成
        if not os.path.exists(RSS_FILE):
            create_new_rss_feed()
            print(f"新規RSSフィード{RSS_FILE}を作成しました")
            return
            
        # 既存のRSSファイルを読み込む
        with open(RSS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 重複したXML宣言を削除
        content = re.sub(r'<\?xml.*?\?>\s*<\?xml.*?\?>', '<?xml version="1.0" encoding="UTF-8"?>', content)
        
        # 名前空間を登録
        ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
        ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
        
        # XMLを解析
        root = ET.fromstring(content)
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
                
                # URLエンコードされたファイル名を生成
                encoded_filename = urllib.parse.quote(info['file_name'])
                
                # リンク
                link = ET.SubElement(item, 'link')
                link.text = f"{RAW_GITHUB_URL}/{MP3_DIR}/{encoded_filename}"
                
                # 公開日
                pub_date = ET.SubElement(item, 'pubDate')
                pub_date.text = info['pub_date']
                
                # GUID
                guid = ET.SubElement(item, 'guid')
                guid.set('isPermaLink', 'false')
                guid.text = f"{RAW_GITHUB_URL}/{MP3_DIR}/{encoded_filename}"
                
                # エンクロージャ
                enclosure = ET.SubElement(item, 'enclosure')
                enclosure.set('url', f"{RAW_GITHUB_URL}/{MP3_DIR}/{encoded_filename}")
                enclosure.set('length', str(info['file_size']))
                enclosure.set('type', 'audio/mpeg')
                
                # iTunes関連の情報
                itunes_duration = ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}duration')
                itunes_duration.text = info['duration']
                
                itunes_explicit = ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit')
                itunes_explicit.text = 'no'
                
                itunes_author = ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}author')
                itunes_author.text = 'パジ'
        
        # XMLを整形して保存
        xml_str = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
        
        # XML宣言を修正（minidomが追加する余分な行を削除）
        pretty_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml.split('\n', 1)[1]
        
        with open(RSS_FILE, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        print(f"RSSフィードを更新しました: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"処理したMP3ファイル数: {len(mp3_files)}")
        
    except Exception as e:
        print(f"RSSフィードの更新中にエラーが発生しました: {e}")

if __name__ == "__main__":
    print("Spotify Podcast Manager を実行中...")
    update_rss_feed()
    print("処理が完了しました")
