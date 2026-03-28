# Start all services for Py Copilot

$projectRoot = "e:\PY\CODES\py copilot IV"
$backendDir = "$projectRoot\backend"
$frontendDir = "$projectRoot\frontend"

Write-Host "=== Starting Py Copilot Services ===" -ForegroundColor Green

# Function to check if port is in use
function Test-PortInUse {
    param($port)
    $result = netstat -ano | findstr ":$port"
    return $result -ne $null
}

# Function to stop process on port
function Stop-ProcessOnPort {
    param($port)
    $lines = netstat -ano | findstr ":$port"
    foreach ($line in $lines) {
        if ($line -match "LISTENING\s+(\d+)") {
            $pid = $matches[1]
            Write-Host "Stopping process on port $port (PID: $pid)" -ForegroundColor Yellow
            taskkill /F /PID $pid 2>$null
        }
    }
}

# 1. Start ChromaDB Service
Write-Host "`n[1/3] Starting ChromaDB Service (Port 8008)..." -ForegroundColor Cyan
Stop-ProcessOnPort -port 8008
Start-Sleep -Seconds 1

$chromaJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    python chroma_server.py
} -ArgumentList $backendDir

# 2. Start Backend Service
Write-Host "`n[2/3] Starting Backend Service (Port 8007)..." -ForegroundColor Cyan
Stop-ProcessOnPort -port 8007
Start-Sleep -Seconds 1

$backendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8007 --reload
} -ArgumentList $backendDir

# 3. Start Frontend Service
Write-Host "`n[3/3] Starting Frontend Service..." -ForegroundColor Cyan
Stop-ProcessOnPort -port 5173
Stop-ProcessOnPort -port 3000
Stop-ProcessOnPort -port 3001
Stop-ProcessOnPort -port 3002
Stop-ProcessOnPort -port 3003
Start-Sleep -Seconds 1

$frontendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    npm run dev
} -ArgumentList $frontendDir

Write-Host "`n=== All Services Started ===" -ForegroundColor Green
Write-Host "ChromaDB: http://localhost:8008" -ForegroundColor White
Write-Host "Backend: http://localhost:8007" -ForegroundColor White
Write-Host "Frontend: http://localhost:3003 (or auto-assigned port)" -ForegroundColor White

Write-Host "`nPress Ctrl+C to stop all services..." -ForegroundColor Yellow

# Keep script running and show status
while ($true) {
    Start-Sleep -Seconds 10
    
    $chromaRunning = Test-PortInUse -port 8008
    $backendRunning = Test-PortInUse -port 8007
    
    $chromaStatus = if($chromaRunning){"Running"}else{"Stopped"}
    $backendStatus = if($backendRunning){"Running"}else{"Stopped"}
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ChromaDB: $chromaStatus | Backend: $backendStatus" -ForegroundColor Gray
}
