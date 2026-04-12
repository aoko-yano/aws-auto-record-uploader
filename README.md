# AWS Auto Record Uploader

音声ファイルを自動的にAWS S3 Glacierにアップロードするプログラムです。

## 機能

- 指定フォルダから音声ファイルを検出
- AWS S3 Glacierストレージクラスでアップロード
- 既にS3にある同名ファイルをスキップ
- faster-whisper による文字起こし
- 設定ファイルによる柔軟な設定

## 必要な環境

- Docker Desktop for Windows
- AWS認証情報（Access Key ID と Secret Access Key）

## セットアップ

1. `.env`ファイルを作成:
プロジェクトルートに`.env`ファイルを作成し、以下の内容を記述します:
```env
# ソースドライブのパス（必須）
USB_SOURCE_DRIVE=E:\

# ソースドライブ内のフォルダ（オプション、ソースドライブのルートを使用する場合は空欄）
# 例: RECORD または Recordings
USB_SOURCE_FOLDER=RECORD

# コピー先フォルダのパス（必須）
SOURCE_COPY_FOLDER=./usb_copy

# AWS認証情報（必須）
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key

# AWSリージョン（オプション、config.jsonで設定している場合は不要）
AWS_DEFAULT_REGION=ap-northeast-1

# S3バケット名（必須）
AWS_BUCKET_NAME=your-bucket-name

# S3プレフィックス（必須）
AWS_S3_PREFIX=your-s3-prefix

# 一時フォルダのパス（オプション、デフォルト: ./temp_uploads）
# ホスト側のパスを指定します。コンテナ内では /app/temp_uploads にマウントされます
# TEMP_FOLDER=./temp_uploads
```

2. 設定ファイルの編集:
必要な場合、ルートの`config.json`を編集してアップロード対象などを変更してください。
```json
{
  "usb": {
    "audio_extensions": [".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg", ".wma"]
  },
  "aws": {
    "storage_class": "GLACIER",
    "region": "ap-northeast-1"
  },
  "options": {
    "delete_after_upload": true,
    "create_date_folders": true
  },
  "transcription": {
    "enabled": true,
    "model": "large-v3",
    "language": "ja",
    "device": "cpu",
    "compute_type": "int8"
  }
}
```

### 設定項目の説明

- `usb.audio_extensions`: 検出する音声ファイルの拡張子リスト
- `aws.storage_class`: ストレージクラス（"GLACIER", "DEEP_ARCHIVE"など）
- `aws.region`: AWSリージョン
- `options.delete_after_upload`: アップロード後にソース上のファイルを削除するか（現在は使用されていません）
- `options.create_date_folders`: 日付フォルダを作成するか（例: recordings/20240101/）
- `transcription.enabled`: 文字起こしを行うか
- `transcription.model`: 使用する Whisper モデル名
- `transcription.language`: 文字起こし対象の言語
- `transcription.device`: 推論デバイス（例: `cpu`）
- `transcription.compute_type`: faster-whisper の計算精度

## 開発環境

依存管理は `pyproject.toml` に集約されています。ローカルでテストや CLI を使う場合は、プロジェクトルートで以下を実行してください。

```powershell
python -m pip install -e ".[dev]"
```

インストール後は、以下のどちらでも起動できます。

```powershell
aws-auto-record-uploader --config config.json
python -m aws_auto_record_uploader --config config.json
```

## 内部構成

実装コードは `src/aws_auto_record_uploader/` 配下の package にまとめています。Docker 関連ファイルと設定ファイルはルートに置いています。

- `src/aws_auto_record_uploader/cli.py`: CLI エントリーポイント
- `src/aws_auto_record_uploader/app.py`: パイプライン全体の実行順序を管理
- `src/aws_auto_record_uploader/config.py`: `config.json` の読込
- `src/aws_auto_record_uploader/audio_files.py`: 音声ファイル探索と重複除外
- `src/aws_auto_record_uploader/staging.py`: 一時フォルダへのコピーとクリーンアップ
- `src/aws_auto_record_uploader/transcription.py`: Whisper モデル読込と文字起こし
- `src/aws_auto_record_uploader/s3_upload.py`: S3 クライアント生成、既存ファイル確認、アップロード

テストは `tests/` 配下に置き、package 単位で import しています。

## 使用方法

PowerShellで以下を実行してください：
```powershell
.\run.ps1
```

あるいは、バッチファイル run.bat をGUI上から実行してください。

## 注意事項

- アップロード前に必ずソースドライブが接続されていることを確認してください
- S3 Glacierストレージクラスは低コストですが、取得に時間がかかります
- ファイルはWindows側でコピーしてから処理されるため、元のファイルは削除されません

## トラブルシューティング

### AWS認証エラー
```
✗ エラー: AWS認証情報が見つかりません
```
→ `.env`ファイルに`AWS_ACCESS_KEY_ID`と`AWS_SECRET_ACCESS_KEY`が正しく設定されているか確認してください
→ 環境変数が正しく設定されているか確認してください

### ソースフォルダが見つからない
```
✗ エラー: ソースフォルダが見つかりません
```
→ `.env`ファイルの`USB_SOURCE_DRIVE`と`USB_SOURCE_FOLDER`が正しく設定されているか確認してください
→ Windowsのドライブレター（例: `E:\`）が正しく指定されているか確認してください
→ `copy_usb.ps1`が正常に実行されたか確認してください
→ コピー先フォルダ（`SOURCE_COPY_FOLDER`）が存在するか確認してください

### S3バケットが存在しない
→ 指定したバケットが存在するか、適切な権限があるか確認してください

### AWS認証情報が見つからない
→ `.env`ファイルに`AWS_ACCESS_KEY_ID`と`AWS_SECRET_ACCESS_KEY`が設定されているか確認してください
→ `.env`ファイルがプロジェクトルートに存在するか確認してください
→ 環境変数が正しく読み込まれているか確認してください

## License

MIT License. See [LICENSE](LICENSE) for details.
