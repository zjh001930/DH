@echo off
echo 🧹 清理测试环境...

REM 删除旧的测试结果文件
if exist rag_test_results.json (
    del rag_test_results.json
    echo ✅ 删除旧的测试结果文件
)

REM 删除不需要的PowerShell测试脚本（已有Python版本）
if exist test_rag.ps1 (
    del test_rag.ps1
    echo ✅ 删除PowerShell测试脚本（已有Python版本）
)

REM 创建测试目录
if not exist test_results mkdir test_results

echo.
echo ✅ 测试环境清理完成
echo.
echo 📋 当前可用的测试工具:
echo   - test_guide.py          : 测试指南和环境检测
echo   - quick_rag_test.py      : 快速RAG功能测试
echo   - test_rag_effectiveness.py : 完整RAG有效性测试
echo   - check_backend_status.py : 后端状态诊断
echo   - simple_api_test.py     : API响应诊断
echo.
echo 🚀 开始测试:
echo   python test_guide.py
pause