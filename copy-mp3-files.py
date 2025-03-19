#!/usr/bin/env python3
"""
GitHub リポジトリ間でmp3ファイルをコピーするスクリプト
プライベートリポジトリ（paji/voicy）からパブリックリポジトリ（paji/Spotify）へ
mp3_downloadsフォルダ内のファイルをコピーします
"""

import os
import base64
import requests
import json
from datetime import datetime

# GitHub API の設定
GITHUB_API = "https://api.github.com"
# 環境変数から GitHub トークンを取得
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") 
# ソースリポジトリとターゲットリポジトリの設定
SOURCE_REPO_OWNER = "paji"
SOURCE_REPO_NAME = "voicy"
SOURCE_REPO_PATH = "mp3_downloads"
TARGET_REPO_OWNER = "paji"
TARGET_REPO_NAME = "Spotify"
TARGET_REPO_PATH = "mp3_downloads"

# ヘッダー設定
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_source_files():
    """ソースリポジトリからファイル一覧を取得"""
    url = f"{GITHUB_API}/repos/{SOURCE_REPO_OWNER}/{SOURCE_REPO_NAME}/contents/{SOURCE_REPO_PATH}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"ソースリポジトリからのファイル取得に失敗しました: {response.status_code}")
        print(response.text)
        return []
    
    return response.json()

def get_target_files():
    """ターゲットリポジトリからファイル一覧を取得"""
    url = f"{GITHUB_API}/repos/{TARGET_REPO_OWNER}/{TARGET_REPO_NAME}/contents/{TARGET_REPO_PATH}"
    response = requests.get(url, headers=headers)
    
    # ターゲットディレクトリが存在しない場合は空のリストを返す
    if response.status_code == 404:
        return []
    
    if response.status_code != 200:
        print(f"ターゲットリポジトリからのファイル取得に失敗しました: {response.status_code}")
        print(response.text)
        return []
    
    return response.json()

def get_file_content(file_path):
    """ファイルの内容を取得"""
    url = f"{GITHUB_API}/repos/{SOURCE_REPO_OWNER}/{SOURCE_REPO_NAME}/contents/{file_path}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"ファイル内容の取得に失敗しました: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def create_or_update_file(file_path, content, sha=None):
    """ファイルを作成または更新"""
    url = f"{GITHUB_API}/repos/{TARGET_REPO_OWNER}/{TARGET_REPO_NAME}/contents/{file_path}"
    
    # コミットメッセージ
    message = f"Update mp3 file from voicy repository - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    data = {
        "message": message,
        "content": content,
        "branch": "main"  # ブランチ名を指定
    }
    
    # 既存ファイルの更新の場合はSHAを指定
    if sha:
        data["sha"] = sha
    
    response = requests.put(url, headers=headers, data=json.dumps(data))
    
    if response.status_code not in [200, 201]:
        print(f"ファイルの作成/更新に失敗しました: {response.status_code}")
        print(response.text)
        return False
    
    return True

def main():
    """メイン処理"""
    print(f"処理開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ソースリポジトリからファイル一覧を取得
    source_files = get_source_files()
    if not source_files:
        print("ソースファイルが見つかりませんでした。")
        return
    
    # ターゲットリポジトリからファイル一覧を取得
    target_files = get_target_files()
    
    # ターゲットファイルの辞書を作成（ファイル名：SHA）
    target_file_dict = {}
    for file in target_files:
        if file["type"] == "file":
            target_file_dict[file["name"]] = file["sha"]
    
    # ファイルをコピー
    copied_count = 0
    for file in source_files:
        if file["type"] == "file" and file["name"].endswith(".mp3"):
            # ファイルの内容を取得
            file_content = get_file_content(file["path"])
            if not file_content:
                continue
            
            # ターゲットのファイルパス
            target_file_path = f"{TARGET_REPO_PATH}/{file['name']}"
            
            # ファイルが既に存在するか確認
            sha = target_file_dict.get(file["name"])
            
            # ファイルを作成または更新
            result = create_or_update_file(
                target_file_path,
                file_content["content"],
                sha
            )
            
            if result:
                copied_count += 1
                print(f"ファイルをコピーしました: {file['name']}")
    
    print(f"処理完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"コピーしたファイル数: {copied_count}")

if __name__ == "__main__":
    main()