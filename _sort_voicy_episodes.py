#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import datetime
from operator import itemgetter

def sort_voicy_episodes():
    """
    voicy_episodes.jsonファイルを読み込み、配信日時（date）で降順ソートして保存する
    追加エピソードがない場合でも、常にソートを実行する
    """
    # JSONファイルを読み込む
    with open('voicy_episodes.json', 'r', encoding='utf-8') as f:
        episodes = json.load(f)
    
    # 配信日時でソート（降順）
    sorted_episodes = sorted(episodes, key=lambda x: x['date'], reverse=True)
    
    # ソート結果をJSONファイルに書き込む
    with open('voicy_episodes.json', 'w', encoding='utf-8') as f:
        json.dump(sorted_episodes, f, ensure_ascii=False, indent=2)
    
    print(f"エピソードを日付順にソートしました。合計: {len(sorted_episodes)}件")

if __name__ == "__main__":
    sort_voicy_episodes()
