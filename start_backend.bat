@echo off
chcp 65001 >nul
echo ========================================
echo   语义文档搜索引擎 - 后端服务启动
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [2/3] 检查依赖...
pip show sentence-transformers >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

echo [3/3] 启动服务...
echo.
echo 服务将在 http://localhost:5000 启动
echo 按 Ctrl+C 停止服务
echo.

python app.py

pause
