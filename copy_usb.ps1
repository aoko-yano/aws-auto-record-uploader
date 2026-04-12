# ソースフォルダからファイルを一時フォルダにコピーするスクリプト
# 使用方法: .\copy_usb.ps1
# .envファイルから設定を読み取ります

$ErrorActionPreference = "Stop"

# .envファイルから設定を読み取る
function Read-EnvFile {
    param([string]$FilePath)

    if (-not $FilePath) {
        $FilePath = Join-Path $PSScriptRoot ".env"
    }

    $envVars = @{}
    if (Test-Path $FilePath) {
        Get-Content $FilePath | ForEach-Object {
            $line = $_.Trim()
            if ($line -and -not $line.StartsWith("#")) {
                if ($line -match "^([^=]+)=(.*)$") {
                    $key = $matches[1].Trim()
                    $value = $matches[2].Trim()
                    $value = $value -replace '^["'']|["'']$', ''
                    $envVars[$key] = $value
                }
            }
        }
    } else {
        Write-Host "エラー: .envファイルが見つかりません: $FilePath" -ForegroundColor Red
        exit 1
    }
    return $envVars
}

function Test-EnvVars {
    param(
        [hashtable]$envVars,
        [string[]]$requiredVars
    )

    $missingVars = @()
    foreach ($var in $requiredVars) {
        if (-not $envVars.ContainsKey($var) -or [string]::IsNullOrWhiteSpace($envVars[$var])) {
            $missingVars += $var
        }
    }

    if ($missingVars.Count -gt 0) {
        Write-Host "エラー: 以下の必須環境変数が.envファイルに設定されていません:" -ForegroundColor Red
        foreach ($var in $missingVars) {
            Write-Host "  - $var" -ForegroundColor Red
        }
        exit 1
    }
}

function Resolve-RootPath {
    param([string]$relativePath)

    if ([System.IO.Path]::IsPathRooted($relativePath)) {
        return [System.IO.Path]::GetFullPath($relativePath)
    }

    $cleanPath = $relativePath -replace '^\./', '' -replace '^\.\./', ''
    $absolutePath = Join-Path $PSScriptRoot $cleanPath

    return [System.IO.Path]::GetFullPath($absolutePath)
}

$envVars = Read-EnvFile

$requiredVars = @("USB_SOURCE_DRIVE", "SOURCE_COPY_FOLDER")
Test-EnvVars -envVars $envVars -requiredVars $requiredVars

$SourceDrive = $envVars["USB_SOURCE_DRIVE"]
$SourceFolder = $envVars["USB_SOURCE_FOLDER"]
$DestFolder = $envVars["SOURCE_COPY_FOLDER"]

if ($env:DEBUG -eq "1") {
    Write-Host "読み取られた環境変数:" -ForegroundColor Cyan
    Write-Host "  USB_SOURCE_DRIVE: $SourceDrive" -ForegroundColor Gray
    Write-Host "  USB_SOURCE_FOLDER: $SourceFolder" -ForegroundColor Gray
    Write-Host "  SOURCE_COPY_FOLDER: $DestFolder" -ForegroundColor Gray
}

$DestFolder = Resolve-RootPath -relativePath $DestFolder

$sourcePath = if ($SourceFolder) {
    Join-Path $SourceDrive $SourceFolder
} else {
    $SourceDrive
}

if (-not (Test-Path $sourcePath)) {
    Write-Host "エラー: ソースパスが見つかりません: $sourcePath" -ForegroundColor Red
    exit 1
}

Write-Host "ソースフォルダからファイルをコピー中..." -ForegroundColor Cyan
Write-Host "  ソース: $sourcePath" -ForegroundColor Gray
Write-Host "  コピー先: $DestFolder" -ForegroundColor Gray

if (Test-Path $DestFolder) {
    Write-Host "既存のコピー先フォルダを削除中..." -ForegroundColor Yellow
    $maxRetries = 3
    $retryCount = 0
    $deleted = $false

    while ($retryCount -lt $maxRetries -and -not $deleted) {
        try {
            Get-ChildItem -Path $DestFolder -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
            Remove-Item -Path $DestFolder -Recurse -Force -ErrorAction Stop
            $deleted = $true
        } catch {
            $retryCount++
            if ($retryCount -lt $maxRetries) {
                Write-Host "  再試行中... ($retryCount/$maxRetries)" -ForegroundColor Yellow
                Start-Sleep -Seconds 1
            } else {
                Write-Host "警告: フォルダの削除に失敗しました（別のプロセスが使用中の可能性があります）: $_" -ForegroundColor Yellow
                Write-Host "  フォルダをクリアして続行します..." -ForegroundColor Yellow
                Get-ChildItem -Path $DestFolder -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }
}
New-Item -ItemType Directory -Path $DestFolder -Force | Out-Null

try {
    Copy-Item -Path $sourcePath -Destination $DestFolder -Recurse -Force

    Start-Sleep -Milliseconds 500
    $fileCount = (Get-ChildItem -Path $DestFolder -Recurse -File -ErrorAction SilentlyContinue).Count
    Write-Host "✓ コピー完了: $fileCount 個のファイル" -ForegroundColor Green
    Write-Host "  コピー先: $DestFolder" -ForegroundColor Gray
    exit 0
} catch {
    Write-Host "エラー: コピーに失敗しました: $_" -ForegroundColor Red
    exit 1
}
