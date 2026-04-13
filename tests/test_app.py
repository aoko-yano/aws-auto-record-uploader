from unittest.mock import MagicMock

from aws_auto_record_uploader.app import run_pipeline


MINIMAL_CONFIG = {
    "usb": {"audio_extensions": [".mp3", ".wav"]},
    "aws": {"storage_class": "GLACIER", "region": "ap-northeast-1"},
    "options": {"create_date_folders": True},
    "transcription": {
        "enabled": True,
        "model": "large-v3",
        "language": "ja",
        "device": "cpu",
        "compute_type": "int8",
    },
}


def test_run_pipeline_stops_when_source_folder_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SOURCE_FOLDER", str(tmp_path / "missing"))
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.load_config",
        MagicMock(return_value=MINIMAL_CONFIG),
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.create_s3_client",
        MagicMock(return_value=MagicMock()),
    )

    run_pipeline("config.json")

    out = capsys.readouterr().out
    assert "ソースフォルダが見つかりません" in out


def test_run_pipeline_skips_transcription_when_disabled(tmp_path, monkeypatch):
    local_file = tmp_path / "temp" / "rec.mp3"
    local_file.parent.mkdir(parents=True)
    local_file.write_bytes(b"x")

    load_config_mock = MagicMock(return_value={**MINIMAL_CONFIG, "transcription": {**MINIMAL_CONFIG["transcription"], "enabled": False}})
    create_s3_client_mock = MagicMock(return_value=MagicMock())
    find_audio_files_mock = MagicMock(return_value=[tmp_path / "source" / "rec.mp3"])
    list_existing_mock = MagicMock(return_value=set())
    filter_new_files_mock = MagicMock(return_value=[tmp_path / "source" / "rec.mp3"])
    prepare_files_mock = MagicMock(return_value=[local_file])
    upload_to_s3_mock = MagicMock(return_value=["prefix/20260411/rec.mp3"])
    cleanup_temp_mock = MagicMock()
    load_whisper_model_mock = MagicMock()
    transcribe_file_mock = MagicMock()

    monkeypatch.setenv("SOURCE_FOLDER", str(tmp_path / "source"))
    monkeypatch.setenv("TEMP_FOLDER_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("AWS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("AWS_S3_PREFIX", "prefix/")
    (tmp_path / "source").mkdir()

    monkeypatch.setattr("aws_auto_record_uploader.app.load_config", load_config_mock)
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.create_s3_client",
        create_s3_client_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.find_audio_files",
        find_audio_files_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.list_existing_s3_filenames",
        list_existing_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.filter_new_files_by_filename",
        filter_new_files_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.prepare_files",
        prepare_files_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.upload_to_s3",
        upload_to_s3_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.cleanup_temp",
        cleanup_temp_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.load_whisper_model",
        load_whisper_model_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.transcribe_file",
        transcribe_file_mock,
    )

    run_pipeline("config.json")

    load_whisper_model_mock.assert_not_called()
    transcribe_file_mock.assert_not_called()
    cleanup_temp_mock.assert_called_once()


def test_run_pipeline_transcribes_each_local_file_when_enabled(tmp_path, monkeypatch):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    local_file_one = tmp_path / "temp" / "rec1.mp3"
    local_file_two = tmp_path / "temp" / "rec2.mp3"
    local_file_one.parent.mkdir(parents=True)
    local_file_one.write_bytes(b"x")
    local_file_two.write_bytes(b"x")

    s3_client = MagicMock()
    model = MagicMock()

    monkeypatch.setenv("SOURCE_FOLDER", str(source_dir))
    monkeypatch.setenv("TEMP_FOLDER_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("AWS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("AWS_S3_PREFIX", "prefix/")

    monkeypatch.setattr(
        "aws_auto_record_uploader.app.load_config",
        MagicMock(return_value=MINIMAL_CONFIG),
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.create_s3_client",
        MagicMock(return_value=s3_client),
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.find_audio_files",
        MagicMock(return_value=[source_dir / "rec1.mp3", source_dir / "rec2.mp3"]),
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.list_existing_s3_filenames",
        MagicMock(return_value=set()),
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.filter_new_files_by_filename",
        MagicMock(return_value=[source_dir / "rec1.mp3", source_dir / "rec2.mp3"]),
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.prepare_files",
        MagicMock(return_value=[local_file_one, local_file_two]),
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.load_whisper_model",
        MagicMock(return_value=model),
    )
    transcribe_file_mock = MagicMock()
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.transcribe_file",
        transcribe_file_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.upload_to_s3",
        MagicMock(return_value=["prefix/20260411/rec1.mp3"]),
    )
    monkeypatch.setattr("aws_auto_record_uploader.app.cleanup_temp", MagicMock())

    run_pipeline("config.json")

    app_calls = transcribe_file_mock.call_args_list
    assert len(app_calls) == 2
    assert app_calls[0].args == (model, local_file_one, "ja")
    assert app_calls[1].args == (model, local_file_two, "ja")


def test_run_pipeline_skips_transcription_and_upload_for_s3_filename_match(tmp_path, monkeypatch):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    audio_file = source_dir / "R20250806-153138.mp3"
    audio_file.write_bytes(b"x")

    prepare_files_mock = MagicMock()
    load_whisper_model_mock = MagicMock()
    transcribe_file_mock = MagicMock()
    upload_to_s3_mock = MagicMock()
    cleanup_temp_mock = MagicMock()

    monkeypatch.setenv("SOURCE_FOLDER", str(source_dir))
    monkeypatch.setenv("TEMP_FOLDER_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("AWS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("AWS_S3_PREFIX", "prefix/")

    monkeypatch.setattr(
        "aws_auto_record_uploader.app.load_config",
        MagicMock(return_value=MINIMAL_CONFIG),
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.create_s3_client",
        MagicMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.find_audio_files",
        MagicMock(return_value=[audio_file]),
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.list_existing_s3_filenames",
        MagicMock(return_value={"other/folder/r20250806-153138.mp3"}),
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.prepare_files",
        prepare_files_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.load_whisper_model",
        load_whisper_model_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.transcribe_file",
        transcribe_file_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.upload_to_s3",
        upload_to_s3_mock,
    )
    monkeypatch.setattr(
        "aws_auto_record_uploader.app.cleanup_temp",
        cleanup_temp_mock,
    )

    run_pipeline("config.json")

    prepare_files_mock.assert_not_called()
    load_whisper_model_mock.assert_not_called()
    transcribe_file_mock.assert_not_called()
    upload_to_s3_mock.assert_not_called()
    cleanup_temp_mock.assert_not_called()
