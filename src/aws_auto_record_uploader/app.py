import os
from pathlib import Path

from .audio_files import filter_new_files, find_audio_files
from .config import load_config
from .s3_upload import create_s3_client, list_existing_s3_filenames, upload_to_s3
from .staging import cleanup_temp, prepare_files
from .transcription import load_whisper_model, transcribe_file


def run_pipeline(config_path: str = "config.json") -> None:
    """音声アップロードの全体フローを実行する"""
    print("=" * 60)
    print("音声ファイル S3 Glacier アップロード & 文字起こし")
    print("=" * 60)

    config = load_config(config_path)
    s3_client = create_s3_client(config["aws"]["region"])

    source_folder = os.environ.get("SOURCE_FOLDER", "/mnt/source")
    source_path = Path(source_folder)
    temp_folder = Path(os.environ.get("TEMP_FOLDER_PATH", "/app/temp_uploads"))
    bucket_name = os.environ.get("AWS_BUCKET_NAME", "").strip()
    s3_prefix = os.environ.get("AWS_S3_PREFIX", "").strip()

    if not source_path.exists():
        print(f"✗ エラー: ソースフォルダが見つかりません: {source_folder}")
        print("  Windows側で copy_usb.ps1 を実行してファイルをコピーしてください。")
        return

    audio_files = find_audio_files(source_folder, config["usb"]["audio_extensions"])
    if not audio_files:
        print("\nアップロードするファイルがありません。")
        return

    print("\nS3の既存ファイルを確認中...")
    existing = list_existing_s3_filenames(
        s3_client,
        bucket_name,
        s3_prefix,
        config["options"]["create_date_folders"],
    )
    new_files = filter_new_files(audio_files, existing, source_path)
    if not new_files:
        print("\n新規ファイルはありません。処理を終了します。")
        return

    local_files = prepare_files(new_files, source_path, temp_folder)
    if not local_files:
        print("ファイルの準備に失敗しました。処理を中断します。")
        return

    transcription_config = config.get("transcription", {})
    if transcription_config.get("enabled", True):
        print(f"\n文字起こしを実行中 (対象: {len(local_files)}個)")
        model = load_whisper_model(transcription_config)
        language = transcription_config.get("language", "ja")
        for local_file in local_files:
            transcribe_file(model, local_file, language)
    else:
        print("\n文字起こしはスキップされました (transcription.enabled = false)")

    uploaded_keys = upload_to_s3(
        client=s3_client,
        local_files=local_files,
        bucket_name=bucket_name,
        s3_prefix=s3_prefix,
        storage_class=config["aws"]["storage_class"],
        create_date_folders=config["options"]["create_date_folders"],
        temp_folder=temp_folder,
    )
    if not uploaded_keys:
        print("アップロードに失敗しました。処理を中断します。")
        return

    cleanup_temp(temp_folder)

    print("\n" + "=" * 60)
    print("✓ すべての処理が完了しました！")
    print("=" * 60)
