#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import datetime
import time
import re
from feedgen.feed import FeedGenerator
import xml.etree.ElementTree as ET

# 基本設定
PODCAST_DIR = 'docs/podcast'
OUTPUT_FILE = 'docs/podcast.xml'
BASE_URL = 'https://paji.github.io/Spotify'

# ポッドキャスト情報
PODCAST_TITLE = 'Spotify Podcast'
PODCAST_DESCRIPTION = 'Spotify向けのポッドキャスト'
PODCAST_AUTHOR = 'paji'
PODCAST_EMAIL = 'info@example.com'  # 適切なメールアドレスに変更してください
PODCAST_IMAGE = f'{BASE_URL}/podcast_cover.jpg'  # カバー画像がある場合のURL
PODCAST_CATEGORY = 'Technology'

def get_mp3_metadata(filepath):
    """
    ファイル名から簡易的なメタデータを抽出する
    例: '2024-03-19_episode_title.mp3' -> {'date': '2024-03-19', 'title': 'episode title'}
    """
    filename = os.path.basename(filepath)
    # ファイル名から日付とタイトルを抽出する正規表現
    match = re.match(r'(\d{4}-\d{2}-\d{2})_(.+)\.mp3', filename)
    
    if match:
        date_str, title = match.groups()
        title = title.replace('_', ' ')  # アンダースコアをスペースに変換
        try:
            pub_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            return {
                'title': title,
                'date': pub_date,
                'filename': filename
            }
        except ValueError:
            pass
    
    # 日付形式が一致しない場合はファイルの更新日時を使用
    file_mtime = os.path.getmtime(filepath)
    return {
        'title': os.path.splitext(filename)[0].replace('_', ' '),
        'date': datetime.datetime.fromtimestamp(file_mtime),
        'filename': filename
    }

def file_size(filepath):
    """ファイルサイズをバイト単位で返す"""
    return os.path.getsize(filepath)

def generate_rss():
    fg = FeedGenerator()
    fg.load_extension('podcast')
    
    # フィード基本情報の設定
    fg.title(PODCAST_TITLE)
    fg.description(PODCAST_DESCRIPTION)
    fg.author({'name': PODCAST_AUTHOR, 'email': PODCAST_EMAIL})
    fg.link(href=BASE_URL, rel='alternate')
    fg.language('ja')  # 日本語に設定
    fg.lastBuildDate(datetime.datetime.now())
    
    # iTunes固有の設定
    fg.podcast.itunes_category(PODCAST_CATEGORY)
    fg.podcast.itunes_image(PODCAST_IMAGE)
    fg.podcast.itunes_explicit('no')
    
    # mp3ファイル一覧を取得し日付順にソート
    mp3_files = glob.glob(os.path.join(PODCAST_DIR, '*.mp3'))
    mp3_metadata = [get_mp3_metadata(f) for f in mp3_files]
    mp3_metadata.sort(key=lambda x: x['date'], reverse=True)
    
    # 各エピソードの情報を追加
    for idx, meta in enumerate(mp3_metadata):
        filepath = os.path.join(PODCAST_DIR, meta['filename'])
        file_url = f"{BASE_URL}/podcast/{meta['filename']}"
        
        fe = fg.add_entry()
        fe.id(file_url)
        fe.title(meta['title'])
        fe.description(f"Episode {len(mp3_metadata) - idx}: {meta['title']}")
        fe.pubDate(meta['date'])
        
        # エンクロージャー（メディアファイル）の設定
        fe.enclosure(file_url, str(file_size(filepath)), 'audio/mpeg')
        
        # iTunes固有のエピソード設定
        fe.podcast.itunes_duration(str(int(file_size(filepath) / 16000)))  # 推定の再生時間（秒）
        fe.podcast.itunes_explicit('no')
    
    # RSSの生成と保存
    rss_xml = fg.rss_str(pretty=True)
    
    # 文字化け防止のためUTF-8で明示的に保存
    with open(OUTPUT_FILE, 'wb') as f:
        f.write(rss_xml)
    
    print(f"Podcast RSS feed generated successfully: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_rss()
