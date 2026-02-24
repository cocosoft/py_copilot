@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Py Copilot 系统服务安装脚本
echo ========================================
echo.

set "PROJECT_ROOT=E:\PY\CODES\py copilot IV"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "NSSM_URL=https://nssm.cc/release/nssm-2.24.zip"
set "NSSM_PATH=C:\nssm\nssm.exe"

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 需要管理员权限运行此脚本
    echo 请右键点击脚本，选择"以管理员身份运行"
    pause
    exit /b 1
)

REM 检查NSSM是否已安装
if not exist "%NSSM_PATH%" (
    echo [信息] NSSM未安装，正在下载...
    if not exist "C:\nssm" mkdir "C:\nssm"
    
    echo [提示] 请手动下载NSSM: %NSSM_URL%
    echo [提示] 解压到 C:\nssm 目录
    echo.
    pause
    exit /b 1
)

echo [信息] NSSM已安装: %NSSM_PATH%
echo.

REM 创建后端服务
echo [1/2] 创建后端服务...
"%NSSM_PATH%" install PyCopilotBackend python "%BACKEND_DIR%\app\api\main.py"
"%NSSM_PATH%" set PyCopilotBackend AppDirectory "%BACKEND_DIR%"
"%NSSM_PATH%" set PyCopilotBackend AppEnvironmentExtra "PYTHONPATH=%BACKEND_DIR%"
"%NSSM_PATH%" set PyCopilotBackend DisplayName "Py Copilot Backend Service"
"%NSSM_PATH%" set PyCopilotBackend Description "Py Copilot 后端API服务"
"%NSSM_PATH%" set PyCopilotBackend Start SERVICE_AUTO_START
"%NSSM_PATH%" set PyCopilotBackend AppStopMethodSkip 0
"%NSSM_PATH%" set PyCopilotBackend AppStopMethodConsole 1500
"%NSSM_PATH%" set PyCopilotBackend AppRestartDelay 5000
echo ✓ 后端服务创建成功

REM 创建前端服务
echo [2/2] 创建前端服务...
"%NSSM_PATH%" install PyCopilotFrontend npm "run" "dev"
"%NSSM_PATH%" set PyCopilotFrontend AppDirectory "%FRONTEND_DIR%"
"%NSSM_PATH%" set PyCopilotFrontend DisplayName "Py Copilot Frontend Service"
"%NSSM_PATH%" set PyCopilotFrontend Description "Py Copilot 前端开发服务"
"%NSSM_PATH%" set PyCopilotFrontend Start SERVICE_AUTO_START
"%NSSM_PATH%" set PyCopilotFrontend AppStopMethodSkip 0
"%NSSM_PATH%" set PyCopilotFrontend AppStopMethodConsole 1500
"%NSSM_PATH%" set PyCopilotFrontend AppRestartDelay 5000
echo ✓ 前端服务创建成功

echo.
echo ========================================
echo 服务安装完成！
echo ========================================
echo.
echo 可用命令:
echo   启动服务:   nssm start PyCopilotBackend
echo               nssm start PyCopilotFrontend
echo   停止服务:   nssm stop PyCopilotBackend
echo               nssm stop PyCopilotFrontend
echo   重启服务:   nssm restart PyCopilotBackend
echo               nssm restart PyCopilotFrontend
echo   查看状态:   nssm status PyCopilotBackend
echo               nssm status PyCopilotFrontend
echo   删除服务:   nssm remove PyCopilotBackend confirm
echo               nssm remove PyCopilotFrontend confirm
echo.
echo 或使用Windows服务管理器 (services.msc)
echo.
pause
