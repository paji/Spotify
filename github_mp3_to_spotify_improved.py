#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import requests
import base64
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote

class GitHubMP3Fetcher:
    """GitHubからMP3ファイルを取得するクラス"""
    
    def __init__(self, username, repo, path='', branch=None):
        """
        初期化
        
        Args:
            username (str): GitHubユーザー名
            repo (str): リポジトリ名
            path (str, optional): リポジトリ内のパス
            branch (str, optional): ブランチ名
        """
        self.username = username
        self.repo = repo
        self.path = path
        
        # 環境変数からトークンを取得
        self.token = os.environ.get('GITHUB_TOKEN')
        if not self.token:
            print("警告: GITHUB_TOKENが設定されていません。API制限に達する可能性があります。")
            self.headers = {}
        else:
            self.headers = {"Authorization": f"token {self.token}"}
        
        # ブランチ名を環境変数または引数から取得、デフォルトはmain
        self.branch = branch or os.environ.get('GITHUB_REF_NAME', 'main')
        
        self.base_url = f"https://api.github.com/repos/{username}/{repo}/contents"
        self.raw_url = f"https://raw.githubusercontent.com/{username}/{repo}/{self.branch}"
        
    def fetch_mp3_files(self):
        """
        MP3ファイルを再帰的に取得
        
        Returns:
            list: MP3ファイル情報のリスト
        """
        return self._fetch_files_recursive(self.path, [])
    
    def _fetch_files_recursive(self, current_path, mp3_files):
        """
        ファイルを再帰的に取得
        
        Args:
            current_path (str): 現在のパス
            mp3_files (list): MP3ファイルのリスト
            
        Returns:
            list: 更新されたMP3ファイルのリスト
        """
        url = f"{self.base_url}/{current_path}"
        if current_path:
            url = f"{self.base_url}/{current_path}"
        else:
            url = self.base_url
            
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"エラー: パス '{current_path}' が見つかりません。")
            elif e.response.status_code == 401:
                print("エラー: 認証に失敗しました。トークンを確認してください。")
            else:
                print(f"HTTPエラー: {e}")
            return mp3_files
        except Exception as e:
            print(f"エラー: {e}")
            return mp3_files
            
        items = response.json()
        
        for item in items:
            if item["type"] == "file" and item["name"].lower().endswith(".mp3"):
                # MP3ファイルの情報を取得
                file_path = item["path"]
                file_url = f"{self.raw_url}/{file_path}"
                file_name = item["name"]
                
                # ファイルサイズを取得
                file_size = item["size"]
                
                # 最終更新日を取得
                file_sha = item["sha"]
                commit_url = f"https://api.github.com/repos/{self.username}/{self.repo}/commits?path={quote(file_path)}&sha={self.branch}"
                
                try:
                    commit_response = requests.get(commit_url, headers=self.headers)
                    commit_response.raise_for_status()
                    commits = commit_response.json()
                    if commits:
                        last_commit = commits[0]
                        last_updated = last_commit["commit"]["committer"]["date"]
                    else:
                        last_updated = datetime.now().isoformat()
                except Exception as e:
                    print(f"コミット情報の取得に失敗しました: {e}")
                    last_updated = datetime.now().isoformat()
                
                mp3_files.append({
                    "filename": file_name,
                    "path": file_path,
                    "url": file_url,
                    "size": file_size,
                    "last_updated": last_updated
                })
                
            elif item["type"] == "dir":
                # ディレクトリの場合は再帰的に処理
                dir_path = item["path"]
                self._fetch_files_recursive(dir_path, mp3_files)
                
        return mp3_files

class RSSGenerator:
    """RSSフィードを生成するクラス"""
    
    def __init__(self, mp3_files, config_file=None):
        """
        初期化
        
        Args:
            mp3_files (list): MP3ファイル情報のリスト
            config_file (str, optional): ポッドキャスト設定ファイルのパス
        """
        self.mp3_files = mp3_files
        
        # 既存のポッドキャスト情報を使用
        self.podcast_info = {
            "title": "裏・パジちゃんねる",
            "description": "パジちゃんねるのポッドキャストフィード",
            "link": "https://example.com",
            "language": "ja",
            "copyright": "All rights reserved",
            "webMaster": "example@example.com",
            "ttl": "60",
            "image": {
                "url": "https://example.com/image.jpg",
                "title": "裏・パジちゃんねる",
                "link": "https://example.com"
            },
            "category": "Technology",
            "explicit": "no",
            "author": "Author Name"
        }
    
    def generate_rss(self):
        """
        RSSフィードを生成
        
        Returns:
            str: XML形式のRSSフィード
        """
        # RSSのルート要素を作成
        rss = ET.Element("rss", {
            "version": "2.0",
            "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
            "xmlns:content": "http://purl.org/rss/1.0/modules/content/"
        })
        
        # チャンネル要素を作成
        channel = ET.SubElement(rss, "channel")
        
        # チャンネル情報を追加
        ET.SubElement(channel, "title").text = self.podcast_info["title"]
        ET.SubElement(channel, "description").text = self.podcast_info["description"]
        ET.SubElement(channel, "link").text = self.podcast_info["link"]
        ET.SubElement(channel, "language").text = self.podcast_info["language"]
        ET.SubElement(channel, "copyright").text = self.podcast_info["copyright"]
        ET.SubElement(channel, "webMaster").text = self.podcast_info["webMaster"]
        ET.SubElement(channel, "ttl").text = self.podcast_info["ttl"]
        
        # iTunesの情報を追加
        ET.SubElement(channel, "itunes:explicit").text = self.podcast_info["explicit"]
        ET.SubElement(channel, "itunes:author").text = self.podcast_info["author"]
        ET.SubElement(channel, "itunes:category", {"text": self.podcast_info["category"]})
        
        # イメージ情報を追加
        image = ET.SubElement(channel, "image")
        ET.SubElement(image, "url").text = self.podcast_info["image"]["url"]
        ET.SubElement(image, "title").text = self.podcast_info["image"]["title"]
        ET.SubElement(image, "link").text = self.podcast_info["image"]["link"]
        
        # iTunesのイメージ情報を追加
        ET.SubElement(channel, "itunes:image", {"href": self.podcast_info["image"]["url"]})
        
        # MP3ファイルごとにアイテムを追加
        for mp3_file in self.mp3_files:
            self._add_item(channel, mp3_file)
        
        # XMLを文字列に変換
        tree = ET.ElementTree(rss)
        ET.indent(tree, space="  ", level=0)
        
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_str += ET.tostring(rss, encoding="unicode")
        
        return xml_str
    
    def _add_item(self, channel, mp3_file):
        """
        アイテムを追加
        
        Args:
            channel (Element): チャンネル要素
            mp3_file (dict): MP3ファイル情報
        """
        # 必須フィールドの検証
        if 'url' not in mp3_file or not mp3_file['url']:
            print(f"エラー: URLが不足しているため、アイテムをスキップします: {mp3_file.get('filename', 'unknown')}")
            return
            
        # アイテム要素を作成
        item = ET.SubElement(channel, "item")
        
        # タイトルを設定（ファイル名から拡張子を除去）
        title = mp3_file["filename"].replace(".mp3", "")
        ET.SubElement(item, "title").text = title
        
        # 説明を設定
        description = f"{title} - {self.podcast_info['description']}"
        ET.SubElement(item, "description").text = description
        
        # リンクを設定
        ET.SubElement(item, "link").text = mp3_file["url"]
        
        # 公開日を設定
        pub_date = datetime.fromisoformat(mp3_file["last_updated"].replace("Z", "+00:00"))
        ET.SubElement(item, "pubDate").text = pub_date.strftime("%a, %d %b %Y %H:%M:%S %z")
        
        # GUIDを設定
        ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = mp3_file["url"]
        
        # エンクロージャを設定
        ET.SubElement(item, "enclosure", {
            "url": mp3_file["url"],
            "length": str(mp3_file["size"]),
            "type": "audio/mpeg"
        })
        
        # iTunesの情報を追加
        ET.SubElement(item, "itunes:duration").text = "00:30:00"  # 仮の値
        ET.SubElement(item, "itunes:explicit").text = self.podcast_info["explicit"]

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="GitHubからMP3ファイルを取得してRSSフィードを生成")
    subparsers = parser.add_subparsers(dest="command", help="コマンド")
    
    # fetchコマンド
    fetch_parser = subparsers.add_parser("fetch", help="MP3ファイルを取得")
    fetch_parser.add_argument("--username", "-u", required=True, help="GitHubユーザー名")
    fetch_parser.add_argument("--repo", "-r", required=True, help="リポジトリ名")
    fetch_parser.add_argument("--path", "-p", default="", help="リポジトリ内のパス")
    fetch_parser.add_argument("--branch", "-b", default=None, help="ブランチ名（デフォルト: main）")
    fetch_parser.add_argument("--output", "-o", default="mp3_files.json", help="出力ファイル名")
    
    # generateコマンド
    generate_parser = subparsers.add_parser("generate", help="RSSフィードを生成")
    generate_parser.add_argument("--input", "-i", required=True, help="MP3ファイル情報のJSONファイル")
    generate_parser.add_argument("--output", "-o", default="podcast.xml", help="出力ファイル名")
    
    # allコマンド
    all_parser = subparsers.add_parser("all", help="MP3ファイルを取得してRSSフィードを生成")
    all_parser.add_argument("--username", "-u", required=True, help="GitHubユーザー名")
    all_parser.add_argument("--repo", "-r", required=True, help="リポジトリ名")
    all_parser.add_argument("--path", "-p", default="", help="リポジトリ内のパス")
    all_parser.add_argument("--branch", "-b", default=None, help="ブランチ名（デフォルト: main）")
    all_parser.add_argument("--output", "-o", default="podcast.xml", help="出力ファイル名")
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        # MP3ファイルを取得
        fetcher = GitHubMP3Fetcher(args.username, args.repo, args.path, args.branch)
        mp3_files = fetcher.fetch_mp3_files()
        
        # 結果をJSONファイルに保存
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(mp3_files, f, ensure_ascii=False, indent=2)
            
        print(f"{len(mp3_files)}個のMP3ファイルを{args.output}に保存しました。")
        
    elif args.command == "generate":
        # MP3ファイル情報を読み込み
        with open(args.input, "r", encoding="utf-8") as f:
            mp3_files = json.load(f)
            
        # RSSフィードを生成
        generator = RSSGenerator(mp3_files)
        rss = generator.generate_rss()
        
        # 結果をXMLファイルに保存
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(rss)
            
        print(f"RSSフィードを{args.output}に保存しました。")
        
    elif args.command == "all":
        # MP3ファイルを取得
        fetcher = GitHubMP3Fetcher(args.username, args.repo, args.path, args.branch)
        mp3_files = fetcher.fetch_mp3_files()
        
        # RSSフィードを生成
        generator = RSSGenerator(mp3_files)
        rss = generator.generate_rss()
        
        # 結果をXMLファイルに保存
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(rss)
            
        print(f"{len(mp3_files)}個のMP3ファイルからRSSフィードを{args.output}に保存しました。")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
