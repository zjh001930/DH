@echo off
chcp 65001 >nul
echo ========================================
echo 测试导入的数据
echo ========================================

:: 检查 Docker 服务
docker ps >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker 服务未运行
    pause
    exit /b 1
)

echo 1. 测试 AI 助手知识问答...
curl -s -X POST http://localhost:8000/assistant ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"如何安装软件？\", \"conversation_id\": \"test_knowledge\"}"

echo.
echo.

echo 2. 测试任务引导功能...
curl -s -X POST http://localhost:8000/assistant ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"我想进行FFT分析\", \"conversation_id\": \"test_task\"}"

echo.
echo.

echo 3. 测试 Ollama 模型...
curl -s -X POST http://localhost:11434/api/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"model\": \"qwen2.5:3b-instruct\", \"prompt\": \"你好，请简单介绍一下自己\", \"stream\": false}"

echo.
echo.

echo ========================================
echo 测试完成！
echo ========================================

pause