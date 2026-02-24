@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:check_port
set PORT=%1
set RESULT=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    set RESULT=1
    goto :eof
)
goto :eof

:test_backend
echo 测试后端服务...
curl -s -o nul -w "%%{http_code}" http://localhost:8007/api/v1/health 2>nul
if !errorlevel! equ 0 (
    echo ✓ 后端服务正常
    return 0
) else (
    echo ✗ 后端服务异常
    return 1
)

:test_frontend
echo 测试前端服务...
curl -s -o nul -w "%%{http_code}" http://localhost:5173 2>nul
if !errorlevel! equ 0 (
    echo ✓ 前端服务正常
    return 0
) else (
    echo ✗ 前端服务异常
    return 1
)

:main
cls
echo ========================================
echo Py Copilot 服务健康检查
echo ========================================
echo.

call :check_port 8007
set BACKEND_PORT=!RESULT!

call :check_port 5173
set FRONTEND_PORT=!RESULT!

echo [端口检查]
if "!BACKEND_PORT!"=="1" (
    echo   后端 (8007): ✓ 监听中
) else (
    echo   后端 (8007): ✗ 未监听
)

if "!FRONTEND_PORT!"=="1" (
    echo   前端 (5173): ✓ 监听中
) else (
    echo   前端 (5173): ✗ 未监听
)

echo.
echo [服务检查]
call :test_backend
call :test_frontend

echo.
echo ========================================
echo 按任意键退出，或按R重新检查...
choice /c R /n /t 5 /d R /m "5秒后自动重新检查..."
if !errorlevel! equ 1 (
    goto :main
)
