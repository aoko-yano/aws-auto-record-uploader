import sys
from unittest.mock import MagicMock

from aws_auto_record_uploader.transcription import load_whisper_model, transcribe_file


def _make_segment(start: float, text: str):
    segment = MagicMock()
    segment.start = start
    segment.text = text
    return segment


def test_load_whisper_model_uses_config_values(monkeypatch):
    whisper_module = MagicMock()
    monkeypatch.setitem(sys.modules, "faster_whisper", whisper_module)

    model = load_whisper_model(
        {
            "model": "large-v3",
            "device": "cpu",
            "compute_type": "int8",
        }
    )

    whisper_module.WhisperModel.assert_called_once_with("large-v3", device="cpu", compute_type="int8")
    assert model == whisper_module.WhisperModel.return_value


def test_transcribe_file_writes_timestamped_text(tmp_path):
    audio_file = tmp_path / "rec.mp3"
    audio_file.write_bytes(b"fake")
    model = MagicMock()
    model.transcribe.return_value = (
        [_make_segment(0.0, " こんにちは"), _make_segment(3.5, " 世界")],
        MagicMock(),
    )

    result = transcribe_file(model, audio_file, "ja")

    assert result == audio_file.with_suffix(".txt")
    assert result.read_text(encoding="utf-8") == "[0.0s] こんにちは\n[3.5s] 世界\n"


def test_transcribe_file_returns_none_on_failure(tmp_path):
    audio_file = tmp_path / "rec.mp3"
    audio_file.write_bytes(b"fake")
    model = MagicMock()
    model.transcribe.side_effect = RuntimeError("model error")

    result = transcribe_file(model, audio_file, "ja")

    assert result is None
