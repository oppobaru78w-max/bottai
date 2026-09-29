@echo off
chcp 65001 >nul
title Push ke GitHub - bottai
echo ====================================================
echo   Push Kode ke GitHub: oppobaru78w-max/bottai
echo ====================================================
echo.
echo Mengirim kode ke https://github.com/oppobaru78w-max/bottai.git ...
echo (Jika muncul jendela browser, silakan login/klik Sign In to GitHub)
echo.

git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ====================================================
    echo [SUKSES] Kode berhasil terkirim ke GitHub!
    echo Sekarang Anda bisa langsung membuka Vercel atau Render.
    echo ====================================================
) else (
    echo.
    echo ====================================================
    echo [INFO] Jika gagal login, Anda juga bisa memasukkan
    echo Personal Access Token GitHub saat diminta.
    echo ====================================================
)

pause
