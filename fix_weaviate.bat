@echo off
chcp 65001 >nul
echo ========================================
echo 修复 Weaviate 客户端问题
echo ========================================

echo 1. 卸载现有的 Weaviate 包...
pip uninstall weaviate weaviate-client -y

echo.
echo 2. 安装兼容的 Weaviate 客户端版本...
pip install weaviate-client==3.25.3

echo.
echo 3. 验证安装...
python -c "import weaviate; print('Weaviate 客户端安装成功！')"

if errorlevel 1 (
    echo 安装验证失败，尝试备用方案...
    pip install weaviate-client==3.24.2
    python -c "import weaviate; print('Weaviate 客户端备用版本安装成功！')"
)

echo.
echo ========================================
echo 修复完成！现在可以运行数据导入脚本
echo ========================================

pause