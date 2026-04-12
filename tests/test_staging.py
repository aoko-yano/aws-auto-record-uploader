from aws_auto_record_uploader.staging import cleanup_temp, prepare_files


def test_prepare_files_copies_audio_into_temp_folder(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    audio_file = source_dir / "nested" / "audio.mp3"
    audio_file.parent.mkdir()
    audio_file.write_bytes(b"mp3data")

    temp_dir = tmp_path / "temp"

    result = prepare_files([audio_file], source_dir, temp_dir)

    assert result == [temp_dir / "nested" / "audio.mp3"]
    assert result[0].read_bytes() == b"mp3data"


def test_prepare_files_skips_unrelated_path(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_file = outside_dir / "audio.mp3"
    outside_file.write_bytes(b"mp3data")
    temp_dir = tmp_path / "temp"

    result = prepare_files([outside_file], source_dir, temp_dir)

    assert result == []


def test_cleanup_temp_removes_nested_files_and_directories(tmp_path):
    temp_dir = tmp_path / "temp"
    nested_dir = temp_dir / "subdir"
    nested_dir.mkdir(parents=True)
    (temp_dir / "audio.mp3").write_bytes(b"x")
    (nested_dir / "audio.txt").write_text("hello", encoding="utf-8")

    cleanup_temp(temp_dir)

    assert list(temp_dir.iterdir()) == []
