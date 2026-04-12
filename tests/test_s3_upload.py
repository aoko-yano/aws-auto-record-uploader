from datetime import datetime
from unittest.mock import MagicMock, patch

from aws_auto_record_uploader.s3_upload import (
    create_s3_client,
    list_existing_s3_filenames,
    upload_to_s3,
)


def test_create_s3_client_uses_requested_region():
    with patch("aws_auto_record_uploader.s3_upload.boto3.client") as mock_client:
        client = create_s3_client("ap-northeast-1")

    mock_client.assert_called_once_with("s3", region_name="ap-northeast-1")
    assert client == mock_client.return_value


def test_list_existing_s3_filenames_returns_normalized_relative_paths():
    client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {"Contents": [{"Key": "prefix/20260101/A/R20250101.MP3"}]},
        {"Contents": [{"Key": "prefix/20260101/B/R20250102.mp3"}]},
    ]
    client.get_paginator.return_value = paginator

    result = list_existing_s3_filenames(client, "bucket", "prefix/", True)

    assert result == {"a/r20250101.mp3", "b/r20250102.mp3"}


def test_upload_to_s3_returns_empty_when_bucket_missing(tmp_path):
    audio_file = tmp_path / "rec.mp3"
    audio_file.write_bytes(b"x")

    result = upload_to_s3(
        client=MagicMock(),
        local_files=[audio_file],
        bucket_name="",
        s3_prefix="prefix/",
        storage_class="GLACIER",
        create_date_folders=True,
        temp_folder=tmp_path,
        now=datetime(2026, 4, 11, 0, 0, 0),
    )

    assert result == []


def test_upload_to_s3_uploads_audio_and_txt(tmp_path):
    client = MagicMock()
    audio_file = tmp_path / "rec.mp3"
    audio_file.write_bytes(b"x")
    txt_file = tmp_path / "rec.txt"
    txt_file.write_text("[0.0s] hello\n", encoding="utf-8")
    now = datetime(2026, 4, 11, 0, 0, 0)

    result = upload_to_s3(
        client=client,
        local_files=[audio_file],
        bucket_name="bucket",
        s3_prefix="prefix/",
        storage_class="GLACIER",
        create_date_folders=True,
        temp_folder=tmp_path,
        now=now,
    )

    assert result == ["prefix/20260411/rec.mp3", "prefix/20260411/rec.txt"]
    first_call = client.upload_file.call_args_list[0]
    first_extra = first_call.kwargs["ExtraArgs"]
    assert first_extra["StorageClass"] == "GLACIER"
    assert first_extra["Metadata"]["original_path"] == "rec.mp3"

    second_call = client.upload_file.call_args_list[1]
    second_extra = second_call.kwargs["ExtraArgs"]
    assert "StorageClass" not in second_extra


def test_upload_to_s3_preserves_nested_relative_path_and_normalizes_prefix(tmp_path):
    client = MagicMock()
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    audio_file = nested_dir / "rec.mp3"
    audio_file.write_bytes(b"x")

    result = upload_to_s3(
        client=client,
        local_files=[audio_file],
        bucket_name="bucket",
        s3_prefix="prefix",
        storage_class="GLACIER",
        create_date_folders=True,
        temp_folder=tmp_path,
        now=datetime(2026, 4, 11, 0, 0, 0),
    )

    assert result == ["prefix/20260411/nested/rec.mp3"]


def test_upload_to_s3_uses_flat_key_when_date_folder_disabled(tmp_path):
    client = MagicMock()
    audio_file = tmp_path / "rec.mp3"
    audio_file.write_bytes(b"x")

    result = upload_to_s3(
        client=client,
        local_files=[audio_file],
        bucket_name="bucket",
        s3_prefix="prefix/",
        storage_class="GLACIER",
        create_date_folders=False,
        temp_folder=tmp_path,
        now=datetime(2026, 4, 11, 0, 0, 0),
    )

    assert result == ["prefix/rec.mp3"]
