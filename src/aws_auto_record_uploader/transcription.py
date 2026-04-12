from pathlib import Path
from typing import Any


def load_whisper_model(transcription_config: dict[str, Any]):
    """Whisperモデルを読み込む"""
    model_name = transcription_config.get("model", "large-v3")
    device = transcription_config.get("device", "cpu")
    compute_type = transcription_config.get("compute_type", "int8")

    print(f"\nWhisperモデルを読み込み中: {model_name} ({device}, {compute_type})")
    print("  ※ 初回はモデルのダウンロードが必要なため時間がかかります")

    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    print(f"✓ Whisperモデルを読み込みました: {model_name}")
    return model


def transcribe_file(model, audio_file: Path, language: str) -> Path | None:
    """音声ファイルを文字起こしし、タイムスタンプ付き .txt を同フォルダに保存"""
    txt_path = audio_file.with_suffix(".txt")

    try:
        print(f"  文字起こし中: {audio_file.name}")
        segments, _ = model.transcribe(str(audio_file), language=language, beam_size=5)
        with open(txt_path, "w", encoding="utf-8") as file:
            for segment in segments:
                file.write(f"[{segment.start:.1f}s] {segment.text.strip()}\n")
        print(f"  ✓ 文字起こし完了: {txt_path.name}")
        return txt_path
    except Exception as error:
        print(f"  ✗ 文字起こし失敗: {audio_file.name} - {error}")
        return None
