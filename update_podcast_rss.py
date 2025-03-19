#!/usr/bin/env python3
import os
import re
import datetime
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom

# GitHubリポジトリの情報
GITHUB_USER = "paji"
REPO_NAME = "Spotify"
PODCAST_DIR = "docs/podcast"
RSS_FILE = "docs/podcast.xml"
BASE_URL = f"https://github.com/{GITHUB_USER}/{REPO_NAME}/tree/gh-pages/{PODCAST_DIR}"
RAW_CONTENT_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/gh-pages"

# Podcastの基本情報
PODCAST_TITLE = "My Podcast"
PODCAST_DESCRIPTION = "Podcast feed auto-generated from GitHub repository"
PODCAST_AUTHOR = "Podcast Author"
PODCAST_IMAGE = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/podcast/cover.jpg"
PODCAST_LANGUAGE = "ja"
PODCAST_CATEGORY = "Technology"
PODCAST_EXPLICIT = "no"
PODCAST_OWNER_NAME = PODCAST_AUTHOR
PODCAST_OWNER_EMAIL = "example@example.com"
PODCAST_WEBSITE = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/"

def get_mp3_files():
    """GitHubのリポジトリからmp3ファイルのリストを取得する"""
    response = requests.get(BASE_URL)
    if response.status_code != 200:
        print(f"Error fetching repository: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    mp3_files = []
    
    # GitHubのファイルリストからmp3ファイルを探す
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.endswith('.mp3') and '/blob/' in href:
            # ファイル名を取得
            file_name = os.path.basename(href)
            # ファイルパスを取得
            file_path = f"{PODCAST_DIR}/{file_name}"
            raw_url = f"{RAW_CONTENT_BASE}/{file_path}"
            
            # ファイルの情報を取得
            file_response = requests.head(raw_url)
            size = int(file_response.headers.get('content-length', 0))
            last_modified = file_response.headers.get('last-modified', '')
            
            if last_modified:
                try:
                    pub_date = datetime.datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S GMT')
                except ValueError:
                    pub_date = datetime.datetime.now()
            else:
                pub_date = datetime.datetime.now()
                
            # タイトルはファイル名から推測（.mp3拡張子を除去）
            title = file_name.replace('.mp3', '').replace('_', ' ').replace('-', ' ')
            
            mp3_files.append({
                'title': title,
                'url': raw_url,
                'size': size,
                'type': 'audio/mpeg',
                'pub_date': pub_date,
                'duration': '00:30:00',  # デフォルト値、実際の長さを取得するにはさらなる処理が必要
                'description': f"Episode: {title}"
            })
    
    # 公開日時で降順ソート（新しい順）
    mp3_files.sort(key=lambda x: x['pub_date'], reverse=True)
    return mp3_files

def load_existing_rss():
    """既存のRSSファイルを読み込む"""
    try:
        tree = ET.parse(RSS_FILE)
        return tree
    except (ET.ParseError, FileNotFoundError):
        return None

def generate_rss(mp3_files):
    """mp3ファイルのリストからRSSフィードを生成する"""
    # 既存のRSSを読み込み、存在しない場合は新規作成
    existing_tree = load_existing_rss()
    
    if existing_tree:
        root = existing_tree.getroot()
        channel = root.find('channel')
        
        # 既存の<item>要素を削除
        for item in channel.findall('item'):
            channel.remove(item)
    else:
        # 新規RSSの作成
        root = ET.Element('rss')
        root.set('version', '2.0')
        root.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
        root.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
        
        channel = ET.SubElement(root, 'channel')
        
        # チャンネル基本情報
        ET.SubElement(channel, 'title').text = PODCAST_TITLE
        ET.SubElement(channel, 'link').text = PODCAST_WEBSITE
        ET.SubElement(channel, 'language').text = PODCAST_LANGUAGE
        ET.SubElement(channel, 'description').text = PODCAST_DESCRIPTION
        
        # iTunes固有のタグ
        ET.SubElement(channel, 'itunes:author').text = PODCAST_AUTHOR
        ET.SubElement(channel, 'itunes:summary').text = PODCAST_DESCRIPTION
        ET.SubElement(channel, 'itunes:explicit').text = PODCAST_EXPLICIT
        
        # カバー画像
        image = ET.SubElement(channel, 'itunes:image')
        image.set('href', PODCAST_IMAGE)
        
        # カテゴリ
        category = ET.SubElement(channel, 'itunes:category')
        category.set('text', PODCAST_CATEGORY)
        
        # 所有者情報
        owner = ET.SubElement(channel, 'itunes:owner')
        ET.SubElement(owner, 'itunes:name').text = PODCAST_OWNER_NAME
        ET.SubElement(owner, 'itunes:email').text = PODCAST_OWNER_EMAIL
    
    # 各mp3ファイルをアイテムとして追加
    for mp3 in mp3_files:
        item = ET.SubElement(channel, 'item')
        
        ET.SubElement(item, 'title').text = mp3['title']
        ET.SubElement(item, 'description').text = mp3['description']
        
        # pubDate形式: Wed, 01 Jan 2020 00:00:00 GMT
        pub_date_str = mp3['pub_date'].strftime('%a, %d %b %Y %H:%M:%S GMT')
        ET.SubElement(item, 'pubDate').text = pub_date_str
        
        # エンクロージャー（mp3ファイル）
        enclosure = ET.SubElement(item, 'enclosure')
        enclosure.set('url', mp3['url'])
        enclosure.set('length', str(mp3['size']))
        enclosure.set('type', mp3['type'])
        
        # iTunes固有のタグ
        ET.SubElement(item, 'itunes:duration').text = mp3['duration']
        ET.SubElement(item, 'itunes:author').text = PODCAST_AUTHOR
        ET.SubElement(item, 'itunes:summary').text = mp3['description']
        
        # GUID（一意のID、ここではURLを使用）
        guid = ET.SubElement(item, 'guid')
        guid.set('isPermaLink', 'true')
        guid.text = mp3['url']
    
    # XMLを整形して文字列に変換
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def update_rss_file():
    """RSSファイルを更新する"""
    mp3_files = get_mp3_files()
    if not mp3_files:
        print("No MP3 files found")
        return
    
    print(f"Found {len(mp3_files)} MP3 files")
    
    # RSSフィードを生成
    rss_content = generate_rss(mp3_files)
    
    # RSSファイルを保存
    with open(RSS_FILE, 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    print(f"RSS feed updated: {RSS_FILE}")

if __name__ == "__main__":
    update_rss_file()
