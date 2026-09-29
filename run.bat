@echo off
chcp 65001 >nul
title TikTok AI Bypass - Bot Telegram
echo ====================================================
echo        TikTok AI Video Bypass - Bot Telegram
echo ====================================================
echo.

:: Cek Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python belum terinstal atau tidak ada di PATH!
    echo Silakan install Python 3.10+ dari python.org terlebih dahulu.
    pause
    exit /b 1
)

:: Pastikan dependensi terinstal
echo [1/2] Memeriksa dan menginstal dependensi...
python -m pip install -r requirements.txt --quiet

:: Menjalankan Bot
echo [2/2] Menjalankan Bot Telegram...
echo.
python bot.py

pause
