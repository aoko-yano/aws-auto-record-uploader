FROM python:3.11-slim

WORKDIR /app

# ffmpeg は faster-whisper の音声デコードに必要
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# パッケージ定義とアプリケーションコードをコピー
COPY pyproject.toml README.md ./
COPY src/aws_auto_record_uploader ./src/aws_auto_record_uploader

# 依存パッケージとアプリ本体をインストール
RUN pip install --no-cache-dir .

# エントリーポイント
ENTRYPOINT ["python", "-m", "aws_auto_record_uploader"]
