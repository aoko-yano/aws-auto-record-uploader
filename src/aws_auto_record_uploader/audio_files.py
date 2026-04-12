from pathlib import Path
from typing import Iterable


def find_audio_files(source_folder: str, extensions: Iterable[str]) -> list[Path]:
    """指定フォルダ内の音声ファイルを検索"""
    audio_files: list[Path] = []
    source_path = Path(source_folder)

    if not source_path.exists():
        print(f"✗ 警告: ソースフォルダが存在しません: {source_folder}")
        return audio_files

    print(f"音声ファイルを検索中: {source_folder}")
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

    deduplicated = sorted(set(audio_files))
    print(f"✓ 合計 {len(deduplicated)}個の音声ファイルを発見しました")
    return deduplicated


def filter_new_files(
    audio_files: list[Path],
    existing_filenames: set[str],
    source_folder: str | Path,
) -> list[Path]:
    """S3に未アップロードの音声ファイルのみ返す"""
    source_path = Path(source_folder)
    new_files = []
    skipped = 0
    for audio_file in audio_files:
        try:
            relative_key = audio_file.relative_to(source_path).as_posix().lower()
        except ValueError:
            relative_key = audio_file.name.lower()

        if relative_key in existing_filenames:
            print(f"  スキップ（既存）: {audio_file.name}")
            skipped += 1
        else:
            new_files.append(audio_file)

    print(f"✓ 新規: {len(new_files)}個 / スキップ: {skipped}個")
    return new_files
