#!/usr/bin/env python3
"""
音声ファイルをS3 Glacierにアップロードするプログラム
設定ファイル（config.json）から設定を読み込んで実行します
"""

import json
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class AudioUploader:
    """音声ファイルをS3 Glacierにアップロードするクラス"""
    
    def __init__(self, config_path: str = "config.json"):
        """設定ファイルを読み込んで初期化"""
        self.config = self._load_config(config_path)
        self.s3_client = None
        self._init_s3_client()
        
    def _load_config(self, config_path: str) -> Dict:
        """設定ファイルを読み込む"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✓ 設定ファイルを読み込みました: {config_path}")
            return config
        except FileNotFoundError:
            print(f"✗ エラー: 設定ファイルが見つかりません: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"✗ エラー: 設定ファイルのJSON形式が不正です: {e}")
            sys.exit(1)
    
    def _init_s3_client(self):
        """S3クライアントを初期化"""
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.config['aws']['region']
            )
            print(f"✓ S3クライアントを初期化しました (リージョン: {self.config['aws']['region']})")
        except NoCredentialsError:
            print("✗ エラー: AWS認証情報が見つかりません。コンテナにAWS認証情報がマウントされているか確認してください。")
            sys.exit(1)
    
    def _find_audio_files(self, source_folder: str) -> List[Path]:
        """指定フォルダ内の音声ファイルを検索"""
        audio_files = []
        extensions = self.config['usb']['audio_extensions']
        source_path = Path(source_folder)
        
        if not source_path.exists():
            print(f"✗ 警告: ソースフォルダが存在しません: {source_folder}")
            return audio_files
        
        print(f"音声ファイルを検索中: {source_folder}")
        # 拡張子の大文字小文字のバリエーションを作成
        all_extensions = set()
        for ext in extensions:
            all_extensions.add(ext.lower())
            all_extensions.add(ext.upper())
            all_extensions.add(ext.capitalize())
        
        for ext in all_extensions:
            found = list(source_path.rglob(f"*{ext}"))
            audio_files.extend(found)
            if found:
                print(f"  - {ext}: {len(found)}個のファイルを発見")
        
        # 重複を除去（大文字小文字の違いで同じファイルが検出される可能性があるため）
        audio_files = list(set(audio_files))
        
        print(f"✓ 合計 {len(audio_files)}個の音声ファイルを発見しました")
        return audio_files
    
    def _prepare_files(self, audio_files: List[Path]) -> List[Path]:
        """音声ファイルを一時フォルダに準備（既にコピー済みの場合はそのまま使用）"""
        # 環境変数で指定されたパスを使用（Dockerコンテナ内のマウントパス）
        temp_folder_path = os.environ.get('TEMP_FOLDER_PATH', '/app/temp_uploads')
        temp_folder = Path(temp_folder_path)
        temp_folder.mkdir(parents=True, exist_ok=True)
        
        source_folder = os.environ.get('SOURCE_FOLDER', '/mnt/source')
        source_path = Path(source_folder)
        
        prepared_files = []
        print(f"\nファイルを準備中: {temp_folder}")
        
        for audio_file in audio_files:
            try:
                # ソースフォルダからの相対パスを取得
                relative_path = audio_file.relative_to(source_path)
                dest_path = temp_folder / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # ファイルをコピー
                shutil.copy2(audio_file, dest_path)
                prepared_files.append(dest_path)
                print(f"  ✓ 準備: {audio_file.name}")
            except Exception as e:
                print(f"  ✗ 準備失敗: {audio_file.name} - {e}")
        
        print(f"✓ {len(prepared_files)}個のファイルを準備しました")
        return prepared_files
    
    def _upload_to_s3(self, local_files: List[Path]) -> List[str]:
        """ローカルファイルをS3 Glacierにアップロード"""
        bucket_name = os.environ.get('AWS_BUCKET_NAME', '').strip()
        s3_prefix = os.environ.get('AWS_S3_PREFIX', '').strip()
        storage_class = self.config['aws']['storage_class']
        
        if not bucket_name:
            print("✗ エラー: AWS_BUCKET_NAME環境変数が設定されていません")
            return []
        if not s3_prefix:
            print("✗ エラー: AWS_S3_PREFIX環境変数が設定されていません")
            return []
        
        uploaded_keys = []
        print(f"\nS3にアップロード中: s3://{bucket_name}/{s3_prefix}")
        
        for local_file in local_files:
            try:
                # S3キーを生成
                temp_folder_path = os.environ.get('TEMP_FOLDER_PATH', '/app/temp_uploads')
                relative_path = local_file.relative_to(Path(temp_folder_path))
                
                if self.config['options']['create_date_folders']:
                    date_str = datetime.now().strftime("%Y%m%d")
                    s3_key = f"{s3_prefix}{date_str}/{relative_path.name}"
                else:
                    s3_key = f"{s3_prefix}{relative_path.name}"
                
                # アップロード
                self.s3_client.upload_file(
                    str(local_file),
                    bucket_name,
                    s3_key,
                    ExtraArgs={
                        'StorageClass': storage_class,
                        'Metadata': {
                            'original_path': str(relative_path),
                            'upload_date': datetime.now().isoformat()
                        }
                    }
                )
                uploaded_keys.append(s3_key)
                print(f"  ✓ アップロード: {local_file.name} -> s3://{bucket_name}/{s3_key}")
            except ClientError as e:
                print(f"  ✗ アップロード失敗: {local_file.name} - {e}")
            except Exception as e:
                print(f"  ✗ エラー: {local_file.name} - {e}")
        
        print(f"✓ {len(uploaded_keys)}個のファイルをアップロードしました")
        return uploaded_keys
    
    def _cleanup_temp(self):
        """一時フォルダをクリーンアップ"""
        temp_folder_path = os.environ.get('TEMP_FOLDER_PATH', '/app/temp_uploads')
        temp_folder = Path(temp_folder_path)
        if temp_folder.exists():
            try:
                # マウントされたフォルダ内のファイルのみ削除（フォルダ自体は削除しない）
                for item in temp_folder.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    except Exception as e:
                        # 個別のファイル/フォルダの削除に失敗しても続行
                        pass
                print(f"✓ 一時フォルダの内容をクリーンアップしました: {temp_folder}")
            except Exception as e:
                # マウントされたフォルダは削除できないため、エラーを無視
                print(f"⚠ 一時フォルダのクリーンアップをスキップしました（マウントされたフォルダのため）")
    
    def run(self):
        """メイン処理を実行"""
        print("=" * 60)
        print("音声ファイル S3 Glacier アップロード")
        print("=" * 60)
        
        # ソースフォルダの確認
        source_folder = os.environ.get('SOURCE_FOLDER', '/mnt/source')
        source_path = Path(source_folder)
        
        if not source_path.exists():
            print(f"✗ エラー: ソースフォルダが見つかりません: {source_folder}")
            print("  Windows側で copy_usb.ps1 を実行してファイルをコピーしてください。")
            return
        
        # 音声ファイルの検索
        audio_files = self._find_audio_files(source_folder)
        
        if not audio_files:
            print("\nアップロードするファイルがありません。")
            return
        
        # 一時フォルダにファイルを準備
        local_files = self._prepare_files(audio_files)
        
        if not local_files:
            print("ファイルの準備に失敗しました。処理を中断します。")
            return
        
        # S3にアップロード
        uploaded_keys = self._upload_to_s3(local_files)
        
        if not uploaded_keys:
            print("アップロードに失敗しました。処理を中断します。")
            return
        
        # 一時フォルダをクリーンアップ
        self._cleanup_temp()
        
        print("\n" + "=" * 60)
        print("✓ すべての処理が完了しました！")
        print("=" * 60)


def main():
    """エントリーポイント"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='音声ファイルをS3 Glacierにアップロード'
    )
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help='設定ファイルのパス (デフォルト: config.json)'
    )
    
    args = parser.parse_args()
    
    uploader = AudioUploader(config_path=args.config)
    uploader.run()


if __name__ == "__main__":
    main()
