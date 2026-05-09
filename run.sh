#!/usr/bin/env bash
# Linux 用の実行スクリプト（run.bat / run.ps1 の代替）
# USB ドライブを直接マウントして Docker で処理する（コピー不要）
set -euo pipefail

cd "$(dirname "$0")"

# .env から LINUX_SOURCE_FOLDER を読み込む
USB_SOURCE=$(grep '^LINUX_SOURCE_FOLDER=' .env | cut -d= -f2- | tr -d '\r')

if [ -z "$USB_SOURCE" ]; then
    echo "エラー: .env に LINUX_SOURCE_FOLDER が設定されていません"
    exit 1
fi

if [ ! -d "$USB_SOURCE" ]; then
    echo "エラー: USBドライブが見つかりません: $USB_SOURCE"
    echo "  USBレコーダーをPCに接続してから再実行してください"
    exit 1
fi

# Docker アクセス確認（グループ未設定なら sudo -E を使う）
# sudo -E で環境変数（SOURCE_COPY_FOLDER等）を引き継ぐ
if docker info >/dev/null 2>&1; then
    DC="docker compose"
else
    echo "sudo でDockerを実行します（パスワードを入力してください）"
    DC="sudo -E docker compose"
fi

echo "============================================================"
echo "音声ファイル S3 Glacier アップロード"
echo "============================================================"

echo ""
echo "[0/2] 既存のコンテナを停止中..."
$DC down 2>/dev/null || true
$DC rm -f 2>/dev/null || true

echo ""
echo "[1/2] Dockerイメージをビルド中..."
$DC build

echo ""
echo "[2/2] 処理を実行中..."
SOURCE_COPY_FOLDER="$USB_SOURCE" $DC up --no-log-prefix

echo ""
echo "============================================================"
echo "✓ 完了"
echo "============================================================"
