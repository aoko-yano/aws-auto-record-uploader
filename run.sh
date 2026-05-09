#!/usr/bin/env bash
# Linux 用の実行スクリプト（run.bat / run.ps1 の代替）
# USB ドライブを直接マウントして Docker で処理する（コピー不要）
set -euo pipefail

cd "$(dirname "$0")"

USB_SOURCE="/run/media/aoko-yano/USB DISK/RECORD"

# Docker アクセス確認（グループ未設定なら sudo を使う）
if docker info >/dev/null 2>&1; then
    DC="docker compose"
else
    echo "sudo でDockerを実行します（パスワードを入力してください）"
    DC="sudo docker compose"
fi

if [ ! -d "$USB_SOURCE" ]; then
    echo "エラー: USBドライブが見つかりません: $USB_SOURCE"
    echo "  USBレコーダーをPCに接続してから再実行してください"
    exit 1
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
