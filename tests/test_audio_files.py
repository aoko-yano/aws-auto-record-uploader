from pathlib import Path

from aws_auto_record_uploader.audio_files import (
    filter_new_files,
    filter_new_files_by_filename,
    find_audio_files,
)


def test_find_audio_files_returns_empty_for_missing_folder(tmp_path):
    missing = tmp_path / "missing"

    result = find_audio_files(str(missing), [".mp3", ".wav"])

    assert result == []


def test_find_audio_files_discovers_extensions_case_insensitively(tmp_path):
    (tmp_path / "a.mp3").write_bytes(b"fake")
    (tmp_path / "b.WAV").write_bytes(b"fake")
    (tmp_path / "ignore.txt").write_text("nope", encoding="utf-8")

    result = find_audio_files(str(tmp_path), [".mp3", ".wav"])

    assert {path.name for path in result} == {"a.mp3", "b.WAV"}


def test_find_audio_files_deduplicates_results(tmp_path):
    audio_file = tmp_path / "only.mp3"
    audio_file.write_bytes(b"fake")

    result = find_audio_files(str(tmp_path), [".mp3", ".MP3"])

    assert result == [audio_file]


def test_filter_new_files_skips_existing_relative_paths_case_insensitively(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    new_file = source_dir / "a" / "rec.mp3"
    old_file = source_dir / "b" / "REC.MP3"
    new_file.parent.mkdir()
    old_file.parent.mkdir()

    result = filter_new_files([new_file, old_file], {"b/rec.mp3"}, source_dir)

    assert result == [new_file]


def test_filter_new_files_by_filename_skips_existing_names_anywhere(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    new_file = source_dir / "a" / "new.mp3"
    old_file = source_dir / "b" / "REC.MP3"
    new_file.parent.mkdir()
    old_file.parent.mkdir()

    result = filter_new_files_by_filename(
        [new_file, old_file],
        {"somewhere/else/rec.mp3"},
    )

    assert result == [new_file]
