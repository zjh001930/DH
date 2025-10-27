@echo off
chcp 65001 >nul
echo ========================================
echo AI 助手数据导入工具
echo ========================================

:: 检查项目结构
if not exist "backend" (
    echo 错误: 未找到 backend 目录
    echo 请确保在项目根目录运行此脚本
    pause
    exit /b 1
)

if not exist "backend\data" (
    echo 错误: 未找到 backend\data 目录
    echo 请确保数据目录存在
    pause
    exit /b 1
)

:: 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python
    echo 请确保 Python 已安装并添加到 PATH
    pause
    exit /b 1
)

:: 检查 Docker 服务状态
echo 检查 Docker 服务状态...
docker ps >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker 服务未运行
    echo 请先启动 Docker 服务
    pause
    exit /b 1
)

:: 检查必要的容器是否运行
echo 检查必要的容器...
set CONTAINERS_MISSING=0

docker ps --format "{{.Names}}" | findstr "ollama_host" >nul
if errorlevel 1 (
    echo 警告: ollama_host 容器未运行
    set CONTAINERS_MISSING=1
)

docker ps --format "{{.Names}}" | findstr "weaviate_db" >nul
if errorlevel 1 (
    echo 警告: weaviate_db 容器未运行
    set CONTAINERS_MISSING=1
)

docker ps --format "{{.Names}}" | findstr "postgres_db" >nul
if errorlevel 1 (
    echo 警告: postgres_db 容器未运行
    set CONTAINERS_MISSING=1
)

if %CONTAINERS_MISSING%==1 (
    echo 尝试启动 Docker Compose...
    docker-compose up -d
    echo 等待服务启动...
    timeout /t 30 /nobreak >nul
)

:: 执行数据导入
echo ========================================
echo 开始执行数据导入...
echo ========================================

cd backend
python ingest_data.py

if errorlevel 1 (
    echo ========================================
    echo 数据导入失败！
    echo ========================================
    cd ..
    pause
    exit /b 1
) else (
    echo ========================================
    echo 数据导入成功完成！
    echo ========================================
    cd ..
)

echo.
echo 您现在可以：
echo 1. 访问 http://localhost 使用 Web 界面
echo 2. 运行其他测试脚本验证功能
echo.

pause