import json

import pytest

from aws_auto_record_uploader.config import load_config


def test_load_config_returns_parsed_json(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"aws": {"region": "ap-northeast-1"}}), encoding="utf-8")

    result = load_config(str(config_path))

    assert result == {"aws": {"region": "ap-northeast-1"}}


def test_load_config_exits_for_missing_file(tmp_path):
    missing = tmp_path / "missing.json"

    with pytest.raises(SystemExit) as error:
        load_config(str(missing))

    assert error.value.code == 1
