@echo off
chcp 65001 >nul
echo ========================================
echo   体检报告 AI 解析系统 - 启动脚本
echo ========================================
echo.

REM 检查 Java
java -version 2>&1 | findstr "version" >nul
if errorlevel 1 (
    echo [错误] 未检测到 Java，请先安装 JDK 17+
    pause
    exit /b 1
)

REM 检查 Maven
mvn -version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Maven，请先安装 Maven
    pause
    exit /b 1
)

echo [检查] Java 和 Maven 已就绪
echo.

REM 设置环境变量（如果存在 .env）
if exist .env (
    echo [加载] 从 .env 加载配置
    for /f "usebackq tokens=1,* delims==" %%a in (.env) do (
        set "%%a=%%b"
    )
)

REM 启动服务
echo [启动] 运行 Maven Spring Boot...
echo.
echo 访问地址: http://localhost:8081
echo API 文档: http://localhost:8081/api/medical/health
echo.
echo 按 Ctrl+C 停止服务
echo.

mvn spring-boot:run -f "%~dp0pom.xml"

pause
