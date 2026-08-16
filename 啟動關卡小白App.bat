@echo off
chcp 65001 >nul
title 關卡小白 App
cd /d "%~dp0"
echo ============================================
echo   關卡小白 App 啟動中...
echo   啟動後畫面會印出兩個網址：
echo     Local URL   — 這台電腦自己打開用
echo     Network URL — 手機在「同一個 WiFi」下打開用這個
echo ============================================
echo.
"%~dp0..\python\.venv\Scripts\python.exe" -m streamlit run app.py
pause
