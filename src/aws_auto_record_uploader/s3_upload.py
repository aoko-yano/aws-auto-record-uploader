from datetime import datetime
from pathlib import Path, PurePosixPath

try:
    import boto3
except ModuleNotFoundError:
    class _MissingBoto3:
        def client(self, *args, **kwargs):
            raise ModuleNotFoundError("boto3 is required to create an S3 client")

    boto3 = _MissingBoto3()

try:
    from botocore.exceptions import ClientError
except ModuleNotFoundError:
    ClientError = Exception


def create_s3_client(region: str):
    client = boto3.client("s3", region_name=region)
    print(f"✓ S3クライアントを初期化しました (リージョン: {region})")
    return client


def _normalize_prefix(s3_prefix: str) -> str:
    return s3_prefix if s3_prefix.endswith("/") else f"{s3_prefix}/"


def _normalize_existing_key(key: str, s3_prefix: str, create_date_folders: bool) -> str:
    normalized_prefix = _normalize_prefix(s3_prefix)
    relative_key = key[len(normalized_prefix):] if key.startswith(normalized_prefix) else key
    relative_path = PurePosixPath(relative_key)
    parts = list(relative_path.parts)
    if create_date_folders and parts and len(parts[0]) == 8 and parts[0].isdigit():
        parts = parts[1:]
    return PurePosixPath(*parts).as_posix().lower() if parts else ""


def list_existing_s3_filenames(
    client,
    bucket_name: str,
    s3_prefix: str,
    create_date_folders: bool = False,
) -> set[str]:
    """S3プレフィックス以下に存在するファイル名（小文字）を取得"""
    existing = set()
    normalized_prefix = _normalize_prefix(s3_prefix)
    try:
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name, Prefix=normalized_prefix):
            for obj in page.get("Contents", []):
                normalized_key = _normalize_existing_key(
                    obj["Key"],
                    normalized_prefix,
                    create_date_folders,
                )
                if normalized_key:
                    existing.add(normalized_key)
        print(f"✓ S3に既存の {len(existing)} 個のオブジェクトを確認しました")
    except Exception as error:
        print(f"⚠ S3既存ファイルの確認に失敗しました（全ファイルを処理します）: {error}")

    return existing


def upload_to_s3(
    *,
    client,
    local_files: list[Path],
    bucket_name: str,
    s3_prefix: str,
    storage_class: str,
    create_date_folders: bool,
    temp_folder: str | Path,
    now: datetime | None = None,
) -> list[str]:
    """音声ファイルをGlacierに、文字起こしテキストをStandardでS3にアップロード"""
    if not bucket_name:
        print("✗ エラー: AWS_BUCKET_NAME環境変数が設定されていません")
        return []
    if not s3_prefix:
        print("✗ エラー: AWS_S3_PREFIX環境変数が設定されていません")
        return []

    uploaded_keys = []
    temp_path = Path(temp_folder)
    current_time = now or datetime.now()
    normalized_prefix = _normalize_prefix(s3_prefix)

    print(f"\nS3にアップロード中: s3://{bucket_name}/{normalized_prefix}")

    for local_file in local_files:
        try:
            relative_path = local_file.relative_to(temp_path)
            relative_key = relative_path.as_posix()

            if create_date_folders:
                s3_key = f"{normalized_prefix}{current_time.strftime('%Y%m%d')}/{relative_key}"
            else:
                s3_key = f"{normalized_prefix}{relative_key}"

            client.upload_file(
                str(local_file),
                bucket_name,
                s3_key,
                ExtraArgs={
                    "StorageClass": storage_class,
                    "Metadata": {
                        "original_path": str(relative_path),
                        "upload_date": current_time.isoformat(),
                    },
                },
            )
            uploaded_keys.append(s3_key)
            print(f"  ✓ アップロード [{storage_class}]: {local_file.name} -> {s3_key}")

            txt_path = local_file.with_suffix(".txt")
            if txt_path.exists():
                txt_s3_key = s3_key.rsplit(".", 1)[0] + ".txt"
                client.upload_file(
                    str(txt_path),
                    bucket_name,
                    txt_s3_key,
                    ExtraArgs={
                        "Metadata": {
                            "original_audio": s3_key,
                            "upload_date": current_time.isoformat(),
                        }
                    },
                )
                uploaded_keys.append(txt_s3_key)
                print(f"  ✓ アップロード [STANDARD]: {txt_path.name} -> {txt_s3_key}")

        except ClientError as error:
            print(f"  ✗ アップロード失敗: {local_file.name} - {error}")
        except Exception as error:
            print(f"  ✗ エラー: {local_file.name} - {error}")

    print(f"✓ {len(uploaded_keys)}個のファイルをアップロードしました")
    return uploaded_keys
