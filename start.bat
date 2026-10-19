@echo off
chcp 65001 > nul
title Гладиатор - Голосовой ИИ-Помощник
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ОШИБКА] Виртуальное окружение .venv не найдено.
    pause
    exit /b
)

echo Запуск голосового помощника Гладиатор...
".venv\Scripts\python.exe" main.py
if errorlevel 1 (
    echo.
    echo Помощник завершил работу с ошибкой.
    pause
)
