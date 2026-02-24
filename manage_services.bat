@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

if "%1"=="" (
    echo 用法: manage_services.bat [命令]
    echo.
    echo 可用命令:
    echo   start    - 启动所有服务
    echo   stop     - 停止所有服务
    echo   restart  - 重启所有服务
    echo   status   - 检查服务状态
    echo   backend  - 仅启动后端
    echo   frontend - 仅启动前端
    goto :eof
)

set "COMMAND=%1"
set "COMMAND=%COMMAND:~0,1%%COMMAND:~1%"
set "COMMAND=%COMMAND:~0,1%%COMMAND:~1%"

if "%COMMAND%"=="start" goto :start_all
if "%COMMAND%"=="stop" goto :stop_all
if "%COMMAND%"=="restart" goto :restart_all
if "%COMMAND%"=="status" goto :status
if "%COMMAND%"=="backend" goto :start_backend
if "%COMMAND%"=="frontend" goto :start_frontend

echo 未知命令: %1
echo 运行 'manage_services.bat' 查看可用命令
goto :eof

:start_all
call :start_backend
call :start_frontend
goto :eof

:stop_all
echo.
echo === 停止所有服务 ===
echo 停止后端服务...
call :kill_port 8007
echo 停止前端服务...
call :kill_port 5173
echo ✓ 所有服务已停止
goto :eof

:restart_all
echo.
echo === 重启所有服务 ===
call :stop_all
timeout /t 2 /nobreak >nul
call :start_backend
call :start_frontend
goto :eof

:status
echo.
echo === 服务状态 ===
call :check_port 8007
set BACKEND=!RESULT!
call :check_port 5173
set FRONTEND=!RESULT!

if "!BACKEND!"=="1" (
    echo 后端服务 (8007): ✓ 运行中
) else (
    echo 后端服务 (8007): ✗ 未运行
)

if "!FRONTEND!"=="1" (
    echo 前端服务 (5173): ✓ 运行中
) else (
    echo 前端服务 (5173): ✗ 未运行
)
goto :eof

:start_backend
echo.
echo === 启动后端服务 ===
call :kill_port 8007
cd /d "E:\PY\CODES\py copilot IV\backend"
echo 启动命令: python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8007 --reload
echo 后端服务正在启动...
start "Py Copilot Backend" cmd /k "python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8007 --reload"

for /l %%i in (1,1,10) do (
    timeout /t 1 /nobreak >nul
    call :check_port 8007
    if "!RESULT!"=="1" (
        echo ✓ 后端服务启动成功！
        echo   地址: http://localhost:8007
        goto :eof
    )
    echo   等待服务启动... (%%i/10)
)
echo ✗ 后端服务启动超时
goto :eof

:start_frontend
echo.
echo === 启动前端服务 ===
call :kill_port 5173
cd /d "E:\PY\CODES\py copilot IV\frontend"
echo 启动命令: npm run dev
echo 前端服务正在启动...
start "Py Copilot Frontend" cmd /k "npm run dev"

for /l %%i in (1,1,10) do (
    timeout /t 1 /nobreak >nul
    call :check_port 5173
    if "!RESULT!"=="1" (
        echo ✓ 前端服务启动成功！
        echo   地址: http://localhost:5173
        goto :eof
    )
    echo   等待服务启动... (%%i/10)
)
echo ✗ 前端服务启动超时
goto :eof

:kill_port
set PORT=%1
echo 检查端口 %PORT% 的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    echo   终止进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul
goto :eof

:check_port
set PORT=%1
set RESULT=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    set RESULT=1
    goto :eof
)
goto :eof
