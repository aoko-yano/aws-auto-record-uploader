import json
import sys
from typing import Any


def load_config(config_path: str) -> dict[str, Any]:
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
        print(f"✓ 設定ファイルを読み込みました: {config_path}")
        return config
    except FileNotFoundError:
        print(f"✗ エラー: 設定ファイルが見つかりません: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as error:
        print(f"✗ エラー: 設定ファイルのJSON形式が不正です: {error}")
        sys.exit(1)
