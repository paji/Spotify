#!/usr/bin/env python3
"""
AAC形式のファイル（MP3拡張子で保存されているもの）をMP3形式に変換するスクリプト

使用方法:
python3 convert_aac_to_mp3.py [ディレクトリパス]

引数:
ディレクトリパス - 変換対象のファイルが含まれるディレクトリ（デフォルト: mp3_downloads）
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_ffmpeg():
    """FFmpegがインストールされているか確認"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("FFmpegが利用可能です")
            return True
        else:
            print("FFmpegが見つかりません")
            return False
    except FileNotFoundError:
        print("FFmpegがインストールされていません")
        return False

def install_ffmpeg():
    """FFmpegをインストール"""
    print("FFmpegをインストールしています...")
    try:
        subprocess.run(['sudo', 'apt-get', 'update'], check=True)
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'], check=True)
        print("FFmpegのインストールが完了しました")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpegのインストールに失敗しました: {e}")
        return False

def is_aac_file(file_path):
    """ファイルがAAC形式かどうかを確認"""
    try:
        # ffprobeを使用してファイルのフォーマットを確認
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_name',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 出力からコーデック名を取得
        codec = result.stdout.strip()
        print(f"ファイル {file_path} のコーデック: {codec}")
        
        # AACコーデックの場合はTrue
        return codec.lower() in ['aac']
    except Exception as e:
        print(f"ファイル {file_path} の形式確認中にエラーが発生しました: {e}")
        return False

def convert_aac_to_mp3(file_path, output_dir=None):
    """AAC形式のファイルをMP3形式に変換"""
    try:
        # 入力ファイルのパスを解析
        input_path = Path(file_path)
        
        # 出力ディレクトリが指定されていない場合は入力ファイルと同じディレクトリを使用
        if output_dir is None:
            output_dir = input_path.parent
        else:
            output_dir = Path(output_dir)
            os.makedirs(output_dir, exist_ok=True)
        
        # 一時ファイル名を作成（元のファイル名に _converted を追加）
        temp_output_path = output_dir / f"{input_path.stem}_converted{input_path.suffix}"
        
        # FFmpegを使用してAACからMP3に変換
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-c:a', 'libmp3lame',  # MP3エンコーダを指定
            '-q:a', '2',           # 品質設定（0-9、低いほど高品質）
            '-y',                  # 既存ファイルを上書き
            str(temp_output_path)
        ]
        
        print(f"変換コマンド: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # 変換成功
            print(f"ファイル {file_path} の変換に成功しました")
            
            # バックアップディレクトリを作成
            backup_dir = output_dir / "aac_backup"
            os.makedirs(backup_dir, exist_ok=True)
            
            # 元のファイルをバックアップ
            backup_path = backup_dir / input_path.name
            shutil.copy2(input_path, backup_path)
            print(f"元のファイルをバックアップしました: {backup_path}")
            
            # 変換したファイルを元のファイル名に戻す
            shutil.move(temp_output_path, input_path)
            print(f"変換したファイルを元のパスに移動しました: {input_path}")
            
            return True
        else:
            # 変換失敗
            print(f"ファイル {file_path} の変換に失敗しました")
            print(f"エラー: {result.stderr}")
            
            # 一時ファイルが存在する場合は削除
            if temp_output_path.exists():
                os.remove(temp_output_path)
            
            return False
    except Exception as e:
        print(f"ファイル {file_path} の変換中にエラーが発生しました: {e}")
        return False

def process_directory(directory_path):
    """指定されたディレクトリ内のMP3ファイルを処理"""
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"ディレクトリ {directory} が存在しません")
        return False
    
    # MP3ファイルを検索
    mp3_files = list(directory.glob("*.mp3"))
    print(f"{len(mp3_files)}個のMP3ファイルが見つかりました")
    
    if not mp3_files:
        print(f"ディレクトリ {directory} にMP3ファイルが見つかりません")
        return False
    
    converted_count = 0
    skipped_count = 0
    
    # 各ファイルを処理
    for mp3_file in mp3_files:
        print(f"\n処理中: {mp3_file}")
        
        # ファイルがAAC形式かどうかを確認
        if is_aac_file(mp3_file):
            # AAC形式の場合はMP3に変換
            if convert_aac_to_mp3(mp3_file):
                converted_count += 1
            else:
                print(f"ファイル {mp3_file} の変換に失敗しました")
        else:
            print(f"ファイル {mp3_file} は既にMP3形式またはAAC以外の形式です。スキップします。")
            skipped_count += 1
    
    print(f"\n処理完了:")
    print(f"- 変換されたファイル: {converted_count}")
    print(f"- スキップされたファイル: {skipped_count}")
    print(f"- 合計: {len(mp3_files)}")
    
    return True

def main():
    """メイン関数"""
    # コマンドライン引数からディレクトリパスを取得
    if len(sys.argv) > 1:
        directory_path = sys.argv[1]
    else:
        # デフォルトはmp3_downloadsディレクトリ
        directory_path = "mp3_downloads"
    
    print(f"ディレクトリ {directory_path} 内のMP3ファイルを処理します")
    
    # FFmpegが利用可能か確認
    if not check_ffmpeg():
        # FFmpegがない場合はインストール
        if not install_ffmpeg():
            print("FFmpegのインストールに失敗しました。処理を中止します。")
            return 1
    
    # ディレクトリ内のファイルを処理
    if process_directory(directory_path):
        print("処理が完了しました")
        return 0
    else:
        print("処理に失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(main())
