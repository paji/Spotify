def download_m3u8_to_mp3(m3u8_url, mp3_path, episode_id):
    """m3u8からMP3をダウンロード"""
    print(f"::group::MP3ダウンロード")
    print(f"オーディオURLからMP3をダウンロード中: {m3u8_url}")
    print(f"出力先: {mp3_path}")
    
    try:
        # URLの拡張子を確認
        is_m3u8 = '.m3u8' in m3u8_url.lower()
        is_mp3 = '.mp3' in m3u8_url.lower()
        
        # MP3の場合は直接ダウンロード
        if is_mp3:
            print(f"MP3ファイルを直接ダウンロードします")
            try:
                response = requests.get(m3u8_url, timeout=30)
                if response.status_code == 200:
                    with open(mp3_path, 'wb') as f:
                        f.write(response.content)
                    
                    if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                        file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
                        print(f"MP3ファイルのダウンロードに成功しました: {mp3_path} (サイズ: {file_size_mb:.2f}MB)")
                        print(f"::endgroup::")
                        return mp3_path
                    else:
                        print(f"MP3ファイルが正常にダウンロードされませんでした")
                else:
                    print(f"MP3ファイルのダウンロードに失敗しました: ステータスコード {response.status_code}")
            except Exception as e:
                print(f"MP3ファイルのダウンロード中にエラーが発生しました: {str(e)}")
        
        # m3u8ファイルの場合
        if is_m3u8:
            # m3u8ファイルの内容を取得
            response = requests.get(m3u8_url, timeout=30)
            if response.status_code != 200:
                print(f"m3u8ファイルの取得に失敗しました: ステータスコード {response.status_code}")
                print(f"::endgroup::")
                return None
            
            m3u8_content = response.text
            
            # m3u8ファイルをデバッグ用に保存
            m3u8_debug_path = f"{DEBUG_DIR}/playlist_{episode_id}.m3u8"
            with open(m3u8_debug_path, 'w') as f:
                f.write(m3u8_content)
            print(f"m3u8ファイルを保存しました: {m3u8_debug_path}")
            
            # セグメントURLを抽出
            segment_urls = []
            base_url = '/'.join(m3u8_url.split('/')[:-1]) + '/'
            
            for line in m3u8_content.splitlines():
                if not line.startswith('#') and line.strip():
                    if line.startswith('http'):
                        segment_urls.append(line)
                    else:
                        segment_urls.append(base_url + line)
            
            print(f"セグメント数: {len(segment_urls)}")
            if not segment_urls:
                print(f"セグメントURLが見つかりませんでした")
                print(f"::endgroup::")
                return None
            
            # セグメントをダウンロード - AACファイルとして保存（JSファイルの実装に合わせる）
            segment_files = []
            for i, url in enumerate(segment_urls):
                segment_path = f"{TEMP_DIR}/segment_{i:03d}.aac"  # .ts から .aac に変更
                try:
                    segment_response = requests.get(url, timeout=30)
                    if segment_response.status_code == 200:
                        with open(segment_path, 'wb') as f:
                            f.write(segment_response.content)
                        segment_files.append(segment_path)
                    else:
                        print(f"セグメント {i} のダウンロードに失敗: ステータスコード {segment_response.status_code}")
                except Exception as e:
                    print(f"セグメント {i} のダウンロード中にエラー: {str(e)}")
            
            print(f"ダウンロードしたセグメント数: {len(segment_files)}")
            
            if not segment_files:
                print(f"セグメントのダウンロードに失敗しました")
                print(f"::endgroup::")
                return None
                
            # JSファイルの実装に合わせて、直接バイナリ結合する方法を最初に試す
            print("方法0: 直接バイナリ結合（JSファイルの実装に合わせる）")
            try:
                with open(mp3_path, 'wb') as outfile:
                    for segment in segment_files:
                        if os.path.exists(segment):
                            with open(segment, 'rb') as infile:
                                shutil.copyfileobj(infile, outfile)
                
                if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                    file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
                    print(f"バイナリ結合によるMP3ファイルの作成に成功しました: {mp3_path} (サイズ: {file_size_mb:.2f}MB)")
                    
                    # 一時ファイルを削除
                    for segment in segment_files:
                        if os.path.exists(segment):
                            os.remove(segment)
                    
                    print(f"::endgroup::")
                    return mp3_path
                else:
                    print(f"バイナリ結合によるMP3ファイルの作成に失敗しました")
            except Exception as e:
                print(f"バイナリ結合中にエラーが発生しました: {str(e)}")
        
        # 以下は元の実装をフォールバックとして残す
        
        # 方法1: 直接FFmpegを使用してURLからMP3に変換
        print("方法1: 直接FFmpegを使用してURLからMP3に変換")
        try:
            cmd1 = [
                'ffmpeg',
                '-i', m3u8_url,
                '-c:a', 'libmp3lame',
                '-q:a', '2',
                '-y',
                mp3_path
            ]
            print(f"FFmpegコマンド（方法1）を実行: {' '.join(cmd1)}")
            result1 = subprocess.run(cmd1, capture_output=True, text=True)
            
            if result1.returncode == 0:
                print(f"MP3ファイルの作成に成功しました: {mp3_path}")
                if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                    file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
                    print(f"MP3ファイル: {mp3_path} (サイズ: {file_size_mb:.2f}MB)")
                    
                    # 一時ファイルを削除
                    if is_m3u8:
                        for segment in segment_files:
                            if os.path.exists(segment):
                                os.remove(segment)
                    
                    print(f"::endgroup::")
                    return mp3_path
                else:
                    print(f"MP3ファイルが正常に作成されませんでした")
            else:
                print(f"FFmpegエラー（方法1）: {result1.stderr}")
        except Exception as e:
            print(f"方法1でのMP3変換中にエラーが発生しました: {str(e)}")
        
        # m3u8の場合のみ以下の方法を試行
        if is_m3u8:
            # 方法2: セグメントファイルを結合してからMP3に変換
            print("方法2: セグメントファイルを結合してからMP3に変換")
            try:
                # セグメントリストファイルを作成
                segments_list = f"{TEMP_DIR}/segments.txt"
                with open(segments_list, 'w') as f:
                    for segment in segment_files:
                        segment_escaped = segment.replace('\\', '\\\\').replace("'", "\\'")
                        f.write(f"file '{segment_escaped}'\n")
                
                # FFmpegでセグメントファイルを結合
                combined_file = f"{TEMP_DIR}/combined.aac"
                cmd2 = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', segments_list,
                    '-c', 'copy',
                    '-y',
                    combined_file
                ]
                print(f"FFmpegコマンド（方法2-1）を実行: {' '.join(cmd2)}")
                result2 = subprocess.run(cmd2, capture_output=True, text=True)
                
                if result2.returncode == 0 and os.path.exists(combined_file) and os.path.getsize(combined_file) > 0:
                    # 結合したファイルをMP3に変換
                    cmd3 = [
                        'ffmpeg',
                        '-i', combined_file,
                        '-c:a', 'libmp3lame',
                        '-q:a', '2',
                        '-y',
                        mp3_path
                    ]
                    print(f"FFmpegコマンド（方法2-2）を実行: {' '.join(cmd3)}")
                    result3 = subprocess.run(cmd3, capture_output=True, text=True)
                    
                    if result3.returncode == 0:
                        print(f"MP3ファイルの作成に成功しました: {mp3_path}")
                        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                            file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
                            print(f"MP3ファイル: {mp3_path} (サイズ: {file_size_mb:.2f}MB)")
                            
                            # 一時ファイルを削除
                            for segment in segment_files:
                                if os.path.exists(segment):
                                    os.remove(segment)
                            if os.path.exists(segments_list):
                                os.remove(segments_list)
                            if os.path.exists(combined_file):
                                os.remove(combined_file)
                            
                            print(f"::endgroup::")
                            return mp3_path
                        else:
                            print(f"MP3ファイルが正常に作成されませんでした")
                    else:
                        print(f"FFmpegエラー（方法2-2）: {result3.stderr}")
                else:
                    print(f"FFmpegエラー（方法2-1）: {result2.stderr}")
            except Exception as e:
                print(f"方法2でのMP3変換中にエラーが発生しました: {str(e)}")
        
        print(f"すべての方法でMP3変換に失敗しました")
        print(f"::endgroup::")
        return None
    
    except Exception as e:
        print(f"MP3ダウンロード中に予期しないエラーが発生しました: {str(e)}")
        traceback.print_exc()
        print(f"::endgroup::")
        return None
