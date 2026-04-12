import shutil
from pathlib import Path


def prepare_files(audio_files: list[Path], source_folder: str | Path, temp_folder: str | Path) -> list[Path]:
    """音声ファイルを一時フォルダにコピーして準備"""
    source_path = Path(source_folder)
    temp_path = Path(temp_folder)
    temp_path.mkdir(parents=True, exist_ok=True)

    prepared_files = []
    print(f"\nファイルを準備中: {temp_path}")

    for audio_file in audio_files:
        try:
            relative_path = audio_file.relative_to(source_path)
            dest_path = temp_path / relative_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(audio_file, dest_path)
            prepared_files.append(dest_path)
            print(f"  ✓ 準備: {audio_file.name}")
        except Exception as error:
            print(f"  ✗ 準備失敗: {audio_file.name} - {error}")

    print(f"✓ {len(prepared_files)}個のファイルを準備しました")
    return prepared_files


def cleanup_temp(temp_folder: str | Path) -> None:
    """一時フォルダをクリーンアップ"""
    temp_path = Path(temp_folder)
    if not temp_path.exists():
        return

    try:
        for item in temp_path.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception:
                pass
        print(f"✓ 一時フォルダの内容をクリーンアップしました: {temp_path}")
    except Exception:
        print(f"⚠ 一時フォルダのクリーンアップをスキップしました（マウントされたフォルダのため）")
