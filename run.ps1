# ファイルをコピーしてDockerコンテナで処理を実行するスクリプト
# 使用方法: .\run.ps1

# 出力エンコーディングをUTF-8に設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ErrorActionPreference = "Stop"

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "音声ファイル S3 Glacier アップロード" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

# 0. Dockerコンテナを停止（既存のコンテナがフォルダを使用している可能性があるため）
Write-Host "`n[0/4] Dockerコンテナを停止中..." -ForegroundColor Yellow
try {
    docker compose down 2>&1 | Out-Null
} catch {
    # エラーを無視（コンテナが存在しない場合など）
}
# 念のため、コンテナ名で直接削除を試みる
try {
    docker rm -f aws-audio-uploader 2>&1 | Out-Null
} catch {
    # エラーを無視（コンテナが存在しない場合など）
}
# コンテナが完全に停止するまで少し待機
Start-Sleep -Seconds 2

# 1. Dockerコンテナをビルド
Write-Host "`n[1/4] Dockerコンテナをビルド中..." -ForegroundColor Yellow
docker compose build
$buildExitCode = $LASTEXITCODE
if ($null -ne $buildExitCode -and $buildExitCode -ne 0) {
    Write-Host "エラー: Dockerコンテナのビルドに失敗しました" -ForegroundColor Red
    exit 1
}

# 2. ファイルをコピー
Write-Host "`n[2/4] ファイルをコピー中..." -ForegroundColor Yellow
& .\copy_usb.ps1
$copyExitCode = $LASTEXITCODE
if ($null -ne $copyExitCode -and $copyExitCode -ne 0) {
    Write-Host "エラー: ファイルのコピーに失敗しました" -ForegroundColor Red
    exit 1
}

# 3. Dockerコンテナで処理
Write-Host "`n[3/4] Dockerコンテナで処理中..." -ForegroundColor Yellow
docker compose up
