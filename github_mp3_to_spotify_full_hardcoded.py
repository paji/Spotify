#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub MP3 to Spotify RSS
------------------------
このスクリプトはGitHubリポジトリからMP3ファイルを取得し、
Spotify対応のRSSフィードを生成します。
ポッドキャスト情報とGitHub APIトークンはハードコーディングされています。
"""

import os
import json
import requests
import datetime
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom
from urllib.parse import quote


class GitHubMP3Fetcher:
    """GitHubリポジトリからMP3ファイルを取得するクラス"""

    def __init__(self, username, repo, branch='main', path=''):
        """
        初期化メソッド
        
        Args:
            username (str): GitHubユーザー名
            repo (str): リポジトリ名
            branch (str, optional): 取得するブランチ名（デフォルト: main）
            path (str, optional): リポジトリ内の特定パス（デフォルト: ルート）
        """
        self.username = username
        self.repo = repo
        self.branch = branch
        self.path = path
        self.base_url = f"https://api.github.com/repos/{username}/{repo}/contents"
        self.raw_base_url = f"https://raw.githubusercontent.com/{username}/{repo}/{branch}"
        
        # ハードコーディングされたGitHub APIトークン
        self.token = "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"
        self.headers = {"Authorization": f"token {self.token}"}

    def get_files_recursive(self, path=''):
        """
        指定パス以下のファイルを再帰的に取得
        
        Args:
            path (str, optional): 取得するパス
            
        Returns:
            list: 取得したファイルのリスト
        """
        current_path = self.path + path
        url = f"{self.base_url}/{quote(current_path)}" if current_path else self.base_url
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            contents = response.json()
            
            all_files = []
            
            # リストでない場合（単一ファイル）はリストに変換
            if not isinstance(contents, list):
                contents = [contents]
                
            for item in contents:
                if item["type"] == "file" and item["name"].lower().endswith(".mp3"):
                    # MP3ファイルの場合
                    file_path = item["path"]
                    raw_url = f"{self.raw_base_url}/{quote(file_path)}"
                    
                    # ファイル名から情報を抽出
                    filename = os.path.basename(file_path)
                    name_without_ext = os.path.splitext(filename)[0]
                    
                    # ファイルサイズを取得（バイト単位）
                    size = item.get("size", 0)
                    
                    # 最終更新日を取得
                    last_modified = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
                    
                    all_files.append({
                        "title": name_without_ext,
                        "filename": filename,
                        "path": file_path,
                        "url": raw_url,
                        "size": size,
                        "last_modified": last_modified
                    })
                    
                elif item["type"] == "dir":
                    # ディレクトリの場合は再帰的に取得
                    subdir_path = path + "/" + item["name"] if path else item["name"]
                    all_files.extend(self.get_files_recursive(subdir_path))
            
            return all_files
            
        except requests.exceptions.RequestException as e:
            print(f"エラー: {e}")
            return []

    def fetch_mp3_files(self):
        """
        MP3ファイルを取得してJSONに保存
        
        Returns:
            list: 取得したMP3ファイルのリスト
        """
        print(f"{self.username}/{self.repo} リポジトリからMP3ファイルを取得中...")
        mp3_files = self.get_files_recursive()
        
        if not mp3_files:
            print("MP3ファイルが見つかりませんでした。")
            return []
        
        print(f"{len(mp3_files)}個のMP3ファイルが見つかりました。")
        return mp3_files

    def save_to_json(self, mp3_files, output_file="mp3_files.json"):
        """
        MP3ファイルリストをJSONファイルに保存
        
        Args:
            mp3_files (list): MP3ファイルのリスト
            output_file (str, optional): 出力ファイル名
            
        Returns:
            bool: 保存成功時はTrue
        """
        if not mp3_files:
            return False
            
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(mp3_files, f, ensure_ascii=False, indent=2)
            print(f"MP3ファイルリストを {output_file} に保存しました。")
            return True
        except Exception as e:
            print(f"JSONファイルの保存中にエラーが発生しました: {e}")
            return False


class SpotifyRSSGenerator:
    """Spotify対応のRSSフィードを生成するクラス"""

    def __init__(self, mp3_files):
        """
        初期化メソッド
        
        Args:
            mp3_files (list): MP3ファイルのリスト
        """
        self.mp3_files = mp3_files
        
        # ハードコーディングされたポッドキャスト情報
        self.podcast_info = {
            "title": "裏・パジちゃんねる",
            "description": "ブロックチェーンやAIなど最新テクノロジーについての考察を毎日配信、濃密情報はプレミアムへ→ https://voicy.jp/channel/2834/all?premium=1\n\nパジの日々の挑戦を記録していきます",
            "author": "パジ",
            "email": "hajimeataka@gmail.com",
            "language": "ja",
            "category": "Technology",
            "explicit": False,
            "image_url": "https://pbs.twimg.com/profile_images/1616257394815954945/2W90KByr_400x400.jpg",
            "website": "https://voicy.jp/channel/2834/all?premium=1",
            "country": "jp"
        }

    def generate_rss(self):
        """
        RSS XMLを生成
        
        Returns:
            str: 整形されたXML文字列
        """
        # RSSのルート要素を作成
        rss = ET.Element('rss')
        rss.set('version', '2.0')
        rss.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
        rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
        rss.set('xmlns:googleplay', 'http://www.google.com/schemas/play-podcasts/1.0')
        rss.set('xmlns:spotify', 'http://www.spotify.com/ns/rss')
        
        # チャンネル要素
        channel = ET.SubElement(rss, 'channel')
        
        # ポッドキャスト基本情報
        ET.SubElement(channel, 'title').text = self.podcast_info['title']
        ET.SubElement(channel, 'description').text = self.podcast_info['description']
        ET.SubElement(channel, 'link').text = self.podcast_info['website']
        ET.SubElement(channel, 'language').text = self.podcast_info['language']
        ET.SubElement(channel, 'copyright').text = f"Copyright {datetime.datetime.now().year} {self.podcast_info['author']}"
        
        # pubDate（最新エピソードの公開日時）
        if self.mp3_files:
            latest_date = max([datetime.datetime.strptime(file.get('last_modified', '01 Jan 2023 00:00:00 GMT'), 
                                                         '%a, %d %b %Y %H:%M:%S GMT') 
                               for file in self.mp3_files])
            ET.SubElement(channel, 'pubDate').text = latest_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
        else:
            ET.SubElement(channel, 'pubDate').text = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # iTunes固有のタグ
        ET.SubElement(channel, 'itunes:author').text = self.podcast_info['author']
        
        # iTunes:owner
        owner = ET.SubElement(channel, 'itunes:owner')
        ET.SubElement(owner, 'itunes:name').text = self.podcast_info['author']
        ET.SubElement(owner, 'itunes:email').text = self.podcast_info['email']
        
        # iTunes:image
        image = ET.SubElement(channel, 'itunes:image')
        image.set('href', self.podcast_info['image_url'])
        
        # 通常のimage
        img = ET.SubElement(channel, 'image')
        ET.SubElement(img, 'url').text = self.podcast_info['image_url']
        ET.SubElement(img, 'title').text = self.podcast_info['title']
        ET.SubElement(img, 'link').text = self.podcast_info['website']
        
        # カテゴリ
        category = ET.SubElement(channel, 'itunes:category')
        category.set('text', self.podcast_info['category'])
        
        # 露骨な表現
        ET.SubElement(channel, 'itunes:explicit').text = 'yes' if self.podcast_info['explicit'] else 'no'
        
        # Spotifyの要件
        ET.SubElement(channel, 'spotify:countryOfOrigin').text = self.podcast_info['country']
        
        # アイテム（エピソード）を追加
        for mp3_file in sorted(self.mp3_files, key=lambda x: x.get('last_modified', ''), reverse=True):
            self._add_item(channel, mp3_file)
        
        # XMLを整形して文字列として返す
        rough_string = ET.tostring(rss, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')

    def _add_item(self, channel, mp3_file):
        """
        チャンネルにアイテム（エピソード）を追加
        
        Args:
            channel (Element): チャンネル要素
            mp3_file (dict): MP3ファイル情報
        """
        item = ET.SubElement(channel, 'item')
        
        # タイトルと説明
        title = mp3_file.get('title', os.path.splitext(mp3_file['filename'])[0])
        ET.SubElement(item, 'title').text = title
        
        # 説明（ファイル名をデフォルトとして使用）
        description = mp3_file.get('description', f"Episode: {title}")
        ET.SubElement(item, 'description').text = description
        ET.SubElement(item, 'itunes:summary').text = description
        
        # 公開日
        pub_date = mp3_file.get('last_modified', datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'))
        ET.SubElement(item, 'pubDate').text = pub_date
        
        # GUIDとリンク
        guid = ET.SubElement(item, 'guid')
        guid.set('isPermaLink', 'false')
        guid.text = mp3_file['url']
        ET.SubElement(item, 'link').text = mp3_file['url']
        
        # エンクロージャー（MP3ファイル）
        enclosure = ET.SubElement(item, 'enclosure')
        enclosure.set('url', mp3_file['url'])
        enclosure.set('length', str(mp3_file.get('size', 0)))
        enclosure.set('type', 'audio/mpeg')
        
        # iTunes固有のタグ
        ET.SubElement(item, 'itunes:author').text = self.podcast_info['author']
        ET.SubElement(item, 'itunes:duration').text = mp3_file.get('duration', '00:30:00')  # デフォルト30分
        
        # エピソード画像（指定がなければポッドキャスト全体の画像を使用）
        episode_image = mp3_file.get('image_url', self.podcast_info['image_url'])
        image = ET.SubElement(item, 'itunes:image')
        image.set('href', episode_image)
        
        # 露骨な表現（エピソード固有の設定がなければポッドキャスト全体の設定を使用）
        explicit = mp3_file.get('explicit', self.podcast_info['explicit'])
        ET.SubElement(item, 'itunes:explicit').text = 'yes' if explicit else 'no'

    def save_to_file(self, output_file="podcast.xml"):
        """
        生成したRSSをファイルに保存
        
        Args:
            output_file (str, optional): 出力ファイル名
            
        Returns:
            bool: 保存成功時はTrue
        """
        try:
            rss_content = self.generate_rss()
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(rss_content)
            print(f"RSSフィードを {output_file} に保存しました。")
            
            # ポッドキャスト設定も保存（参考用）
            with open("podcast_config.json", 'w', encoding='utf-8') as f:
                json.dump(self.podcast_info, f, ensure_ascii=False, indent=2)
            print("ポッドキャスト設定を podcast_config.json に保存しました。")
            
            return True
        except Exception as e:
            print(f"RSSファイルの保存中にエラーが発生しました: {e}")
            return False


def fetch_mp3_files_from_github(args):
    """
    GitHubからMP3ファイルを取得する関数
    
    Args:
        args (Namespace): コマンドライン引数
        
    Returns:
        list: 取得したMP3ファイルのリスト
    """
    # コマンドライン引数から情報を取得
    username = args.username
    repo = args.repo
    branch = args.branch
    path = args.path
    output_file = args.output
    
    if not username:
        username = input("GitHubユーザー名を入力してください: ")
    if not repo:
        repo = input("リポジトリ名を入力してください: ")
    if branch == 'main':
        branch_input = input(f"ブランチ名を入力してください（デフォルト: {branch}）: ").strip()
        branch = branch_input if branch_input else branch
    if not path:
        path = input("リポジトリ内のパスを入力してください（オプション、Enterでスキップ）: ").strip()
    
    fetcher = GitHubMP3Fetcher(username, repo, branch, path)
    mp3_files = fetcher.fetch_mp3_files()
    
    if mp3_files and output_file:
        fetcher.save_to_json(mp3_files, output_file)
        
    return mp3_files


def generate_rss_feed(args, mp3_files=None):
    """
    RSSフィードを生成する関数
    
    Args:
        args (Namespace): コマンドライン引数
        mp3_files (list, optional): MP3ファイルのリスト（指定がなければJSONから読み込み）
        
    Returns:
        bool: 生成成功時はTrue
    """
    input_file = args.input
    output_file = args.output
    
    # MP3ファイルリストを読み込み
    if not mp3_files:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                mp3_files = json.load(f)
        except Exception as e:
            print(f"MP3ファイルリストの読み込みに失敗しました: {e}")
            return False
    
    # RSSフィードを生成
    try:
        generator = SpotifyRSSGenerator(mp3_files)
        return generator.save_to_file(output_file)
        
    except Exception as e:
        print(f"RSSフィード生成中にエラーが発生しました: {e}")
        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='GitHubからMP3ファイルを取得し、Spotify対応のRSSフィードを生成します')
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')
    
    # fetchコマンド
    fetch_parser = subparsers.add_parser('fetch', help='GitHubからMP3ファイルを取得')
    fetch_parser.add_argument('--username', '-u', help='GitHubユーザー名')
    fetch_parser.add_argument('--repo', '-r', help='リポジトリ名')
    fetch_parser.add_argument('--branch', '-b', default='main', help='ブランチ名（デフォルト: main）')
    fetch_parser.add_argument('--path', '-p', default='', help='リポジトリ内のパス（デフォルト: ルート）')
    fetch_parser.add_argument('--output', '-o', default='mp3_files.json', help='出力JSONファイル名（デフォルト: mp3_files.json）')
    
    # generateコマンド
    generate_parser = subparsers.add_parser('generate', help='RSSフィードを生成')
    generate_parser.add_argument('--input', '-i', default='mp3_files.json', help='入力JSONファイル名（デフォルト: mp3_files.json）')
    generate_parser.add_argument('--output', '-o', default='podcast.xml', help='出力XMLファイル名（デフォルト: podcast.xml）')
    
    # allコマンド（fetchとgenerateを連続実行）
    all_parser = subparsers.add_parser('all', help='MP3ファイルの取得からRSSフィード生成まで一括実行')
    all_parser.add_argument('--username', '-u', help='GitHubユーザー名')
    all_parser.add_argument('--repo', '-r', help='リポジトリ名')
    all_parser.add_argument('--branch', '-b', default='main', help='ブランチ名（デフォルト: main）')
    all_parser.add_argument('--path', '-p', default='', help='リポジトリ内のパス（デフォルト: ルート）')
    all_parser.add_argument('--json', '-j', default='mp3_files.json', help='中間JSONファイル名（デフォルト: mp3_files.json）')
    all_parser.add_argument('--output', '-o', default='podcast.xml', help='出力XMLファイル名（デフォルト: podcast.xml）')
    
    args = parser.parse_args()
    
    # コマンドが指定されていない場合はヘルプを表示
    if not args.command:
        parser.print_help()
        return
    
    # コマンドに応じた処理を実行
    if args.command == 'fetch':
        fetch_mp3_files_from_github(args)
    elif args.command == 'generate':
        generate_rss_feed(args)
    elif args.command == 'all':
        # fetchとgenerateを連続実行
        fetch_args = argparse.Namespace(
            username=args.username,
            repo=args.repo,
            branch=args.branch,
            path=args.path,
            output=args.json
        )
        
        generate_args = argparse.Namespace(
            input=args.json,
            output=args.output
        )
        
        mp3_files = fetch_mp3_files_from_github(fetch_args)
        if mp3_files:
            generate_rss_feed(generate_args, mp3_files)


if __name__ == "__main__":
    main()
