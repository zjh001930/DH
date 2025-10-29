@echo off
echo 启动后端服务...
echo ========================

cd /d "%~dp0"
cd backend

echo 当前目录: %CD%
echo.

echo 启动Flask应用 (端口8000)...
python app.py

pause