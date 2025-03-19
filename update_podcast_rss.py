name: Update Podcast RSS Feed

on:
  schedule:
    - cron: '3 * * * *'  # 毎時間3分目に実行
  workflow_dispatch:  # 手動実行も可能

jobs:
  update-rss:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # リポジトリのコンテンツを変更する権限を明示的に付与
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # 完全な履歴をチェックアウト
          
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4 lxml
          
      - name: Run RSS update script
        run: python update_podcast_rss.py
        
      - name: Commit and push if changed
        run: |
          git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add docs/podcast.xml
          git diff --quiet && git diff --staged --quiet || git commit -m "Update podcast RSS feed"
          git push
