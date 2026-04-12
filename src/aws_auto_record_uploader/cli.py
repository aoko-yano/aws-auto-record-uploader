import argparse

from .app import run_pipeline


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="音声ファイルをS3 Glacierにアップロードし、文字起こしを行う"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.json",
        help="設定ファイルのパス (デフォルト: config.json)",
    )

    args = parser.parse_args()
    run_pipeline(args.config)
