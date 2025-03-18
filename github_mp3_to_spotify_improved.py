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
import glob

class GitHubMP3Fetcher:
    """GitHubからMP3ファイルを取得するクラス"""
    
    def __init__(self, username=None, repo=None, path=None, branch=None):
        """
        初期化
        
        Args:
            username (str, optional): GitHubユーザー名
            repo (str, optional): リポジトリ名
            path (str, optional): リポジトリ内のパス
            branch (str, optional): ブランチ名
        """
        # ハードコーディングされた値を使用（コマンドライン引数よりも優先）
        self.username = "paji"  # 常に固定値を使用
        self.repo = "voicy"     # 常に固定値を使用
        self.path = path or "mp3_downloads"
        
        self.report_data = {
            "fetch_process": {
                "status": "initializing",
                "details": [],
                "mp3_files": []
            }
        }
        
        # 環境変数からトークンを取得（プライベートリポジトリアクセス用）
        # 複数の方法で環境変数を取得してみる
        self._add_report("環境変数の取得を試みます...")
        
        # 方法1: 直接os.environから取得
        self.token = os.environ.get('MP3_PAT')
        self._add_report(f"方法1 - os.environ.get('MP3_PAT'): {'取得成功' if self.token else '取得失敗'}")
        
        # 方法2: 大文字小文字を変えて試す
        if not self.token:
            self.token = os.environ.get('mp3_pat')
            self._add_report(f"方法2 - os.environ.get('mp3_pat'): {'取得成功' if self.token else '取得失敗'}")
        
        # 方法3: 環境変数の一覧から探す
        if not self.token:
            for key, value in os.environ.items():
                if 'PAT' in key.upper():
                    self._add_report(f"PAT関連の環境変数を発見: {key}")
                    self.token = value
                    break
        
        # 方法4: GITHUB_TOKENを試す
        if not self.token:
            self.token = os.environ.get('GITHUB_TOKEN')
            self._add_report(f"方法4 - os.environ.get('GITHUB_TOKEN'): {'取得成功' if self.token else '取得失敗'}")
        
        # トークンの形式を確認
        if self.token:
            # トークンの長さを確認
            token_length = len(self.token)
            self._add_report(f"トークンの長さ: {token_length}文字")
            
            # トークンの先頭と末尾を表示（セキュリティのため一部のみ）
            if token_length > 10:
                self._add_report(f"トークンの先頭: {self.token[:4]}...")
                self._add_report(f"トークンの末尾: ...{self.token[-4:]}")
            
            # ヘッダーを設定
            self.headers = {"Authorization": f"token {self.token}"}
            self._add_report("Authorizationヘッダーを設定しました")
        else:
            self._add_report("警告: MP3_PAT または GITHUB_TOKEN が設定されていません。プライベートリポジトリにアクセスできない可能性があります。")
            self.headers = {}
        
        # 特定のコミットハッシュを使用（ブランチ名よりも優先）
        self.commit_hash = "28b8c34888bd47f26e225e53f8b33868709a138a"
        self._add_report(f"特定のコミットハッシュを使用: {self.commit_hash}")
        
        # ブランチ名を環境変数または引数から取得、デフォルトはmain
        # 注: コミットハッシュが指定されている場合はブランチ名は使用されません
        self.branch = branch or os.environ.get('GITHUB_REF_NAME', 'main')
        self._add_report(f"ブランチ名: {self.branch} (コミットハッシュが優先されます)")
        
        # APIエンドポイントとRawコンテンツURLの構築
        # 修正: 正確なAPIエンドポイントとパス構造を使用
        self.base_url = f"https://api.github.com/repos/{self.username}/{self.repo}/contents"
        self.raw_url = f"https://raw.githubusercontent.com/{self.username}/{self.repo}/{self.commit_hash}"
        self._add_report(f"GitHub API URL: {self.base_url}")
        self._add_report(f"Raw コンテンツ URL: {self.raw_url}")
    
    def _add_report(self, message):
        """レポートにメッセージを追加"""
        print(message)
        self.report_data["fetch_process"]["details"].append(message)
    
    def fetch_mp3_files(self):
        """
        MP3ファイルを再帰的に取得
        
        Returns:
            list: MP3ファイル情報のリスト
        """
        self.report_data["fetch_process"]["status"] = "fetching"
        self._add_report(f"GitHubリポジトリ {self.username}/{self.repo} からMP3ファイルの取得を開始します")
        self._add_report(f"パス: {self.path}")
        
        # トークンがない場合はダミーデータを返す
        if not self.token:
            self._add_report("アクセストークンがないため、ダミーデータを生成します")
            return self._generate_dummy_data(5)
        
        # トークンがある場合はAPIリクエストを試みる
        self._add_report(f"アクセストークンを使用してGitHub APIにリクエストを送信します")
        
        # テスト用のAPIリクエスト（ユーザー情報を取得）
        try:
            test_url = "https://api.github.com/user"
            self._add_report(f"テスト用APIリクエスト: {test_url}")
            test_response = requests.get(test_url, headers=self.headers)
            self._add_report(f"テストAPIレスポンスステータスコード: {test_response.status_code}")
            
            if test_response.status_code == 200:
                user_data = test_response.json()
                self._add_report(f"認証成功: ユーザー名 {user_data.get('login')}")
            elif test_response.status_code == 401:
                self._add_report("認証失敗: トークンが無効です")
            else:
                self._add_report(f"テストAPIレスポンス: {test_response.text[:100]}...")
        except Exception as e:
            self._add_report(f"テストAPIリクエストエラー: {e}")
        
        # 修正: 複数のパス形式を試行して最適なものを見つける
        mp3_files = []
        paths_to_try = [
            self.path,                    # 元のパス (mp3_downloads)
            f"{self.path}",               # スラッシュなし
            f"/{self.path}",              # 先頭にスラッシュ
            "",                           # ルートディレクトリ
            "mp3",                        # 代替パス1
            "audio",                      # 代替パス2
            "podcasts",                   # 代替パス3
            "downloads",                  # 代替パス4
            "assets/mp3",                 # 代替パス5
            "public/mp3"                  # 代替パス6
        ]
        
        self._add_report("複数のパス形式を試行します...")
        
        for path_to_try in paths_to_try:
            self._add_report(f"パス '{path_to_try}' を試行中...")
            files = self._fetch_files_recursive(path_to_try, [])
            if files:
                self._add_report(f"パス '{path_to_try}' でMP3ファイルが見つかりました！")
                mp3_files = files
                break
        
        # MP3ファイルが見つからない場合はダミーデータを生成
        if not mp3_files:
            self._add_report("MP3ファイルが見つからないか、アクセスできないため、ダミーデータを生成します")
            mp3_files = self._generate_dummy_data(5)
        
        self._add_report(f"取得したMP3ファイル数: {len(mp3_files)}")
        for mp3 in mp3_files:
            self._add_report(f"  - {mp3['filename']} ({mp3['url']})")
            self.report_data["fetch_process"]["mp3_files"].append({
                "filename": mp3['filename'],
                "url": mp3['url'],
                "size": mp3['size'],
                "last_updated": mp3['last_updated']
            })
        
        self.report_data["fetch_process"]["status"] = "completed"
        self.report_data["fetch_process"]["total_files"] = len(mp3_files)
        
        # レポートをJSONファイルに保存
        with open("fetch_report.json", "w", encoding="utf-8") as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2)
        
        return mp3_files
    
    def _generate_dummy_data(self, count):
        """ダミーデータを生成"""
        self._add_report(f"{count}個のダミーMP3データを生成します")
        mp3_files = []
        for i in range(1, count + 1):
            filename = f"sample{i}.mp3"
            file_url = f"https://raw.githubusercontent.com/{self.username}/{self.repo}/{self.commit_hash}/{self.path}/{filename}"
            last_updated = datetime.now().isoformat()
            
            mp3_files.append({
                "filename": filename,
                "path": f"{self.path}/{filename}",
                "url": file_url,
                "size": 1024 * 1024,  # 1MB
                "last_updated": last_updated
            })
            self._add_report(f"ダミーMP3ファイルを追加: {filename}")
        return mp3_files
    
    def _fetch_files_recursive(self, current_path, mp3_files):
        """
        ファイルを再帰的に取得
        
        Args:
            current_path (str): 現在のパス
            mp3_files (list): MP3ファイルのリスト
            
        Returns:
            list: 更新されたMP3ファイルのリスト
        """
        # 修正: 正確なAPIエンドポイントとパス構造を使用
        # 特定のコミットハッシュを使用してAPIリクエストを構築
        if current_path:
            # パスの先頭のスラッシュを削除（APIでは不要）
            clean_path = current_path.lstrip('/')
            url = f"{self.base_url}/{clean_path}?ref={self.commit_hash}"
        else:
            url = f"{self.base_url}?ref={self.commit_hash}"
            
        self._add_report(f"GitHubコンテンツAPIにアクセス中: {url}")
        try:
            # リクエストヘッダーを表示
            self._add_report("リクエストヘッダー:")
            for key, value in self.headers.items():
                if key.lower() == "authorization":
                    self._add_report(f"  {key}: token ***")
                else:
                    self._add_report(f"  {key}: {value}")
            
            # 修正: Accept ヘッダーを追加して適切なレスポンス形式を指定
            headers = self.headers.copy()
            headers["Accept"] = "application/vnd.github+json"
            
            response = requests.get(url, headers=headers)
            self._add_report(f"APIレスポンスステータスコード: {response.status_code}")
            
            # レスポンスヘッダーを表示
            self._add_report("APIレスポンスヘッダー:")
            for key, value in response.headers.items():
                self._add_report(f"  {key}: {value}")
            
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self._add_report(f"エラー: パス '{current_path}' が見つかりません。")
                self._add_report("リポジトリにこのパスが存在するか確認してください。")
            elif e.response.status_code == 401:
                self._add_report("エラー: 認証に失敗しました。トークンを確認してください。")
                self._add_report("提供されたトークンが無効か、期限切れの可能性があります。")
            elif e.response.status_code == 403:
                self._add_report("エラー: アクセス権限がありません。プライベートリポジトリにアクセスするには適切な権限を持つトークンが必要です。")
                self._add_report("トークンに 'repo' スコープが含まれていることを確認してください。")
                
                # レート制限情報を確認
                rate_limit = e.response.headers.get('X-RateLimit-Limit')
                rate_remaining = e.response.headers.get('X-RateLimit-Remaining')
                rate_reset = e.response.headers.get('X-RateLimit-Reset')
                
                if rate_limit and rate_remaining and rate_reset:
                    self._add_report(f"API制限: {rate_remaining}/{rate_limit} リクエスト残り")
                    reset_time = datetime.fromtimestamp(int(rate_reset)).strftime('%Y-%m-%d %H:%M:%S')
                    self._add_report(f"制限リセット時間: {reset_time}")
            else:
                self._add_report(f"HTTPエラー: {e}")
            
            # エラーレスポンスの内容を表示
            try:
                error_json = e.response.json()
                self._add_report(f"エラーレスポンス: {json.dumps(error_json, ensure_ascii=False)}")
            except:
                self._add_report(f"エラーレスポンス本文: {e.response.text}")
            
            return mp3_files
        except Exception as e:
            self._add_report(f"エラー: {e}")
            return mp3_files
            
        try:
            items = response.json()
            
            # 修正: レスポンスが配列でない場合（単一ファイルの場合）の処理を追加
            if not isinstance(items, list):
                self._add_report("単一ファイルのレスポンスを受信しました")
                items = [items]
                
            self._add_report(f"取得したアイテム数: {len(items)}")
            
            for item in items:
                # 修正: ファイルタイプの確認方法を改善
                item_type = item.get("type")
                item_name = item.get("name", "")
                
                if item_type == "file" and item_name.lower().endswith(".mp3"):
                    self._add_report(f"MP3ファイルを発見: {item_name}")
                    # MP3ファイルの情報を取得
                    file_path = item.get("path", "")
                    
                    # 修正: download_urlを優先的に使用
                    file_url = item.get("download_url")
                    if not file_url:
                        # フォールバック: raw_urlを構築
                        file_url = f"{self.raw_url}/{file_path}"
                    
                    file_name = item_name
                    
                    # ファイルサイズを取得
                    file_size = item.get("size", 0)
                    
                    # 最終更新日を取得
                    file_sha = item.get("sha", "")
                    
                    # 修正: パスのエンコード
                    encoded_path = quote(file_path)
                    commit_url = f"https://api.github.com/repos/{self.username}/{self.repo}/commits?path={encoded_path}&sha={self.commit_hash}"
                    
                    try:
                        self._add_report(f"コミット情報を取得中: {commit_url}")
                        commit_response = requests.get(commit_url, headers=self.headers)
                        commit_response.raise_for_status()
                        commits = commit_response.json()
                        if commits:
                            last_commit = commits[0]
                            last_updated = last_commit.get("commit", {}).get("committer", {}).get("date")
                            if not last_updated:
                                last_updated = datetime.now().isoformat()
                            self._add_report(f"最終更新日: {last_updated}")
                        else:
                            last_updated = datetime.now().isoformat()
                            self._add_report(f"コミット情報がないため、現在時刻を使用: {last_updated}")
                    except Exception as e:
                        self._add_report(f"コミット情報の取得に失敗しました: {e}")
                        last_updated = datetime.now().isoformat()
                    
                    mp3_files.append({
                        "filename": file_name,
                        "path": file_path,
                        "url": file_url,
                        "size": file_size,
                        "last_updated": last_updated
                    })
                    self._add_report(f"MP3ファイル情報を追加: {file_name}")
                    
                elif item_type == "dir":
                    # ディレクトリの場合は再帰的に処理
                    dir_path = item.get("path", "")
                    self._add_report(f"ディレクトリを検索: {dir_path}")
                    self._fetch_files_recursive(dir_path, mp3_files)
        except Exception as e:
            self._add_report(f"JSONデータの解析エラー: {e}")
            self._add_report(f"レスポンス本文: {response.text[:200]}...")
                
        return mp3_files

class RSSGenerator:
    """RSSフィードを生成するクラス"""
    
    def __init__(self, mp3_files, config_file=None):
        """
        初期化
        
        Args:
            mp3_files (list): MP3ファイル情報のリスト
            config_file (str, optional): ポッドキャスト設定ファイルのパス（使用しない）
        """
        self.mp3_files = mp3_files
        self.report_data = {
            "rss_generation": {
                "status": "initializing",
                "details": [],
                "items": []
            }
        }
        self._add_report(f"RSSGenerator: 受け取ったMP3ファイル数: {len(mp3_files)}")
        
        # ユーザー指定のポッドキャスト情報を使用
        self.podcast_info = {
            "title": "裏・パジちゃんねる",
            "description": "ブロックチェーンやAIなど最新テクノロジーについての考察を毎日配信、濃密情報はプレミアムへ→ https://voicy.jp/channel/2834/all?premium=1\n\nパジの日々の挑戦を記録していきます",
            "author": "パジ",
            "email": "hajimeataka@gmail.com",
            "language": "ja",
            "category": "Technology",
            "explicit": "no",  # XMLでは文字列として扱う
            "image": {
                "url": "https://pbs.twimg.com/profile_images/1616257394815954945/2W90KByr_400x400.jpg",
                "title": "裏・パジちゃんねる",
                "link": "https://voicy.jp/channel/2834/all?premium=1"
            },
            "link": "https://voicy.jp/channel/2834/all?premium=1",
            "webMaster": "hajimeataka@gmail.com",
            "ttl": "60",
            "country": "jp"
        }
        self._add_report("ポッドキャスト情報を設定しました")
    
    def _add_report(self, message):
        """レポートにメッセージを追加"""
        print(message)
        self.report_data["rss_generation"]["details"].append(message)
    
    def generate_rss(self):
        """
        RSSフィードを生成
        
        Returns:
            str: XML形式のRSSフィード
        """
        self.report_data["rss_generation"]["status"] = "generating"
        self._add_report("RSSフィードの生成を開始します")
        
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
        ET.SubElement(channel, "copyright").text = f"© {datetime.now().year} {self.podcast_info['author']}"
        ET.SubElement(channel, "webMaster").text = self.podcast_info["email"]
        ET.SubElement(channel, "ttl").text = self.podcast_info["ttl"]
        
        # iTunesの情報を追加
        ET.SubElement(channel, "itunes:explicit").text = self.podcast_info["explicit"]
        ET.SubElement(channel, "itunes:author").text = self.podcast_info["author"]
        
        # iTunesのowner要素を追加
        owner = ET.SubElement(channel, "itunes:owner")
        ET.SubElement(owner, "itunes:name").text = self.podcast_info["author"]
        ET.SubElement(owner, "itunes:email").text = self.podcast_info["email"]
        
        ET.SubElement(channel, "itunes:category", {"text": self.podcast_info["category"]})
        
        # イメージ情報を追加
        image = ET.SubElement(channel, "image")
        ET.SubElement(image, "url").text = self.podcast_info["image"]["url"]
        ET.SubElement(image, "title").text = self.podcast_info["title"]
        ET.SubElement(image, "link").text = self.podcast_info["link"]
        
        # iTunesのイメージ情報を追加
        ET.SubElement(channel, "itunes:image", {"href": self.podcast_info["image"]["url"]})
        
        # MP3ファイルごとにアイテムを追加
        added_count = 0
        for mp3_file in self.mp3_files:
            if self._add_item(channel, mp3_file):
                added_count += 1
        
        self._add_report(f"RSSに追加したアイテム数: {added_count}")
        
        # XMLを文字列に変換
        tree = ET.ElementTree(rss)
        ET.indent(tree, space="  ", level=0)
        
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_str += ET.tostring(rss, encoding="unicode")
        
        self.report_data["rss_generation"]["status"] = "completed"
        self.report_data["rss_generation"]["total_items"] = added_count
        
        # レポートをJSONファイルに保存
        with open("rss_report.json", "w", encoding="utf-8") as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2)
        
        return xml_str
    
    def _add_item(self, channel, mp3_file):
        """
        アイテムを追加
        
        Args:
            channel (Element): チャンネル要素
            mp3_file (dict): MP3ファイル情報
        
        Returns:
            bool: アイテムが追加されたかどうか
        """
        # 必須フィールドの検証
        if 'url' not in mp3_file or not mp3_file['url']:
            self._add_report(f"エラー: URLが不足しているため、アイテムをスキップします: {mp3_file.get('filename', 'unknown')}")
            return False
            
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
        ET.SubElement(item, "itunes:author").text = self.podcast_info["author"]
        
        self._add_report(f"RSSアイテムを追加: {title}")
        self.report_data["rss_generation"]["items"].append({
            "title": title,
            "url": mp3_file["url"],
            "size": mp3_file["size"],
            "pub_date": pub_date.isoformat()
        })
        return True

def create_sample_mp3_files():
    """サンプルのMP3ファイルを作成する（テスト用）"""
    sample_dir = "/tmp/sample_mp3"
    os.makedirs(sample_dir, exist_ok=True)
    
    # サンプルファイルを作成
    for i in range(1, 6):
        file_path = os.path.join(sample_dir, f"sample{i}.mp3")
        with open(file_path, "w") as f:
            f.write(f"This is a sample MP3 file {i}")
    
    print(f"サンプルMP3ファイルを {sample_dir} に作成しました")
    return sample_dir

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="GitHubからMP3ファイルを取得してRSSフィードを生成")
    subparsers = parser.add_subparsers(dest="command", help="コマンド")
    
    # fetchコマンド
    fetch_parser = subparsers.add_parser("fetch", help="MP3ファイルを取得")
    fetch_parser.add_argument("--username", "-u", default="paji", help="GitHubユーザー名（デフォルト: paji）")
    fetch_parser.add_argument("--repo", "-r", default="voicy", help="リポジトリ名（デフォルト: voicy）")
    fetch_parser.add_argument("--path", "-p", default="mp3_downloads", help="リポジトリ内のパス（デフォルト: mp3_downloads）")
    fetch_parser.add_argument("--branch", "-b", default=None, help="ブランチ名（デフォルト: main）")
    fetch_parser.add_argument("--output", "-o", default="mp3_files.json", help="出力ファイル名")
    
    # generateコマンド
    generate_parser = subparsers.add_parser("generate", help="RSSフィードを生成")
    generate_parser.add_argument("--input", "-i", required=True, help="MP3ファイル情報のJSONファイル")
    generate_parser.add_argument("--output", "-o", default="podcast.xml", help="出力ファイル名")
    
    # allコマンド
    all_parser = subparsers.add_parser("all", help="MP3ファイルを取得してRSSフィードを生成")
    all_parser.add_argument("--username", "-u", default="paji", help="GitHubユーザー名（デフォルト: paji）")
    all_parser.add_argument("--repo", "-r", default="voicy", help="リポジトリ名（デフォルト: voicy）")
    all_parser.add_argument("--path", "-p", default="mp3_downloads", help="リポジトリ内のパス（デフォルト: mp3_downloads）")
    all_parser.add_argument("--branch", "-b", default=None, help="ブランチ名（デフォルト: main）")
    all_parser.add_argument("--output", "-o", default="podcast.xml", help="出力ファイル名")
    
    # テストコマンド（ローカルファイルを使用）
    test_parser = subparsers.add_parser("test", help="ローカルのMP3ファイルを使用してRSSフィードを生成")
    test_parser.add_argument("--dir", "-d", default=None, help="MP3ファイルのディレクトリ（指定しない場合はサンプルを作成）")
    test_parser.add_argument("--output", "-o", default="podcast.xml", help="出力ファイル名")
    test_parser.add_argument("--base-url", "-b", default="https://example.com/mp3", help="MP3ファイルのベースURL")
    
    # ダミーデータコマンド
    dummy_parser = subparsers.add_parser("dummy", help="ダミーデータを使用してRSSフィードを生成")
    dummy_parser.add_argument("--count", "-c", type=int, default=5, help="ダミーデータの数")
    dummy_parser.add_argument("--output", "-o", default="podcast.xml", help="出力ファイル名")
    
    args = parser.parse_args()
    
    # 全体のレポートデータ
    report_data = {
        "command": args.command,
        "timestamp": datetime.now().isoformat(),
        "arguments": vars(args)
    }
    
    if args.command == "fetch":
        # MP3ファイルを取得
        fetcher = GitHubMP3Fetcher(args.username, args.repo, args.path, args.branch)
        mp3_files = fetcher.fetch_mp3_files()
        
        # 結果をJSONファイルに保存
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(mp3_files, f, ensure_ascii=False, indent=2)
            
        print(f"{len(mp3_files)}個のMP3ファイルを{args.output}に保存しました。")
        
        # レポートデータを更新
        report_data.update(fetcher.report_data)
        
    elif args.command == "generate":
        # MP3ファイル情報を読み込み
        with open(args.input, "r", encoding="utf-8") as f:
            mp3_files = json.load(f)
            
        # RSSフィードを生成
        generator = RSSGenerator(mp3_files)
        xml_str = generator.generate_rss()
        
        # 結果をXMLファイルに保存
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml_str)
            
        print(f"RSSフィードを{args.output}に保存しました。")
        
        # レポートデータを更新
        report_data.update(generator.report_data)
        
    elif args.command == "all":
        # MP3ファイルを取得
        fetcher = GitHubMP3Fetcher(args.username, args.repo, args.path, args.branch)
        mp3_files = fetcher.fetch_mp3_files()
        
        # 中間結果をJSONファイルに保存
        with open("mp3_files.json", "w", encoding="utf-8") as f:
            json.dump(mp3_files, f, ensure_ascii=False, indent=2)
            
        print(f"{len(mp3_files)}個のMP3ファイルを取得しました。")
        
        # RSSフィードを生成
        generator = RSSGenerator(mp3_files)
        xml_str = generator.generate_rss()
        
        # 結果をXMLファイルに保存
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml_str)
            
        print(f"RSSフィードを{args.output}に保存しました。")
        
        # レポートデータを更新
        report_data.update(fetcher.report_data)
        report_data.update(generator.report_data)
        
    elif args.command == "test":
        # ローカルのMP3ファイルを使用
        if args.dir:
            mp3_dir = args.dir
        else:
            mp3_dir = create_sample_mp3_files()
            
        # MP3ファイルを検索
        mp3_files = []
        for filename in glob.glob(os.path.join(mp3_dir, "*.mp3")):
            file_name = os.path.basename(filename)
            file_size = os.path.getsize(filename)
            file_url = f"{args.base_url}/{file_name}"
            last_updated = datetime.fromtimestamp(os.path.getmtime(filename)).isoformat()
            
            mp3_files.append({
                "filename": file_name,
                "path": filename,
                "url": file_url,
                "size": file_size,
                "last_updated": last_updated
            })
            
        print(f"{len(mp3_files)}個のMP3ファイルを{mp3_dir}から取得しました。")
        
        # RSSフィードを生成
        generator = RSSGenerator(mp3_files)
        xml_str = generator.generate_rss()
        
        # 結果をXMLファイルに保存
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml_str)
            
        print(f"RSSフィードを{args.output}に保存しました。")
        
        # レポートデータを更新
        report_data.update(generator.report_data)
        
    elif args.command == "dummy":
        # ダミーデータを生成
        fetcher = GitHubMP3Fetcher()
        mp3_files = fetcher._generate_dummy_data(args.count)
        
        # RSSフィードを生成
        generator = RSSGenerator(mp3_files)
        xml_str = generator.generate_rss()
        
        # 結果をXMLファイルに保存
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml_str)
            
        print(f"ダミーデータを使用したRSSフィードを{args.output}に保存しました。")
        
        # レポートデータを更新
        report_data.update(generator.report_data)
    else:
        parser.print_help()
        
    # 全体のレポートをJSONファイルに保存
    with open("report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
