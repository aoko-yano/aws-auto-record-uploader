@echo off
chcp 65001 >nul
REM ダブルクリックでrun.ps1を実行するバッチファイル
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; & '%~dp0run.ps1'"
if %ERRORLEVEL% NEQ 0 (
    pause
)
