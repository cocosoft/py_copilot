# Service Management Script

function Check-Port {
    param([int]$Port)
    
    try {
        $result = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
        return $result -ne $null
    } catch {
        Write-Host "Error checking port $Port" -ForegroundColor Red
        return $false
    }
}

function Kill-ProcessesOnPort {
    param([int]$Port)
    
    Write-Host "`nChecking processes on port $Port..." -ForegroundColor Yellow
    
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        $pids = @($connections | ForEach-Object { $_.OwningProcess } | Select-Object -Unique)
        
        if ($pids.Count -gt 0) {
            Write-Host "Found $($pids.Count) processes on port $Port, terminating..." -ForegroundColor Yellow
            
            foreach ($pid in $pids) {
                try {
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    Write-Host "  [OK] Terminated PID: $pid" -ForegroundColor Green
                } catch {
                    Write-Host "  [FAIL] Failed to terminate $pid" -ForegroundColor Red
                }
            }
            
            Start-Sleep -Seconds 1
        } else {
            Write-Host "Port $Port is not in use" -ForegroundColor Green
        }
    } catch {
        Write-Host "Error terminating processes on port $Port" -ForegroundColor Red
    }
}

function Start-Backend {
    Write-Host "`n=== Starting Backend Service ===" -ForegroundColor Cyan
    
    Kill-ProcessesOnPort -Port 8007
    
    try {
        Set-Location "E:\PY\CODES\py copilot IV\backend"
        
        $cmd = "python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8007 --reload"
        Write-Host "Command: $cmd" -ForegroundColor Gray
        Write-Host "Starting backend service..." -ForegroundColor Yellow
        
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -WindowStyle Normal
        
        for ($i = 1; $i -le 10; $i++) {
            Start-Sleep -Seconds 1
            if (Check-Port -Port 8007) {
                Write-Host "[OK] Backend service started successfully!" -ForegroundColor Green
                Write-Host "  URL: http://localhost:8007" -ForegroundColor Cyan
                return $true
            }
            Write-Host "  Waiting... ($i/10)" -ForegroundColor Gray
        }
        
        Write-Host "[FAIL] Backend service startup timeout" -ForegroundColor Red
        return $false
    } catch {
        Write-Host "[FAIL] Failed to start backend" -ForegroundColor Red
        return $false
    }
}

function Start-Frontend {
    Write-Host "`n=== Starting Frontend Service ===" -ForegroundColor Cyan
    
    Kill-ProcessesOnPort -Port 5173
    
    try {
        Set-Location "E:\PY\CODES\py copilot IV\frontend"
        
        $cmd = "npm run dev"
        Write-Host "Command: $cmd" -ForegroundColor Gray
        Write-Host "Starting frontend service..." -ForegroundColor Yellow
        
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -WindowStyle Normal
        
        for ($i = 1; $i -le 10; $i++) {
            Start-Sleep -Seconds 1
            if (Check-Port -Port 5173) {
                Write-Host "[OK] Frontend service started successfully!" -ForegroundColor Green
                Write-Host "  URL: http://localhost:5173" -ForegroundColor Cyan
                return $true
            }
            Write-Host "  Waiting... ($i/10)" -ForegroundColor Gray
        }
        
        Write-Host "[FAIL] Frontend service startup timeout" -ForegroundColor Red
        return $false
    } catch {
        Write-Host "[FAIL] Failed to start frontend" -ForegroundColor Red
        return $false
    }
}

function Stop-All {
    Write-Host "`n=== Stopping All Services ===" -ForegroundColor Cyan
    
    Write-Host "Stopping backend..." -ForegroundColor Yellow
    Kill-ProcessesOnPort -Port 8007
    
    Write-Host "Stopping frontend..." -ForegroundColor Yellow
    Kill-ProcessesOnPort -Port 5173
    
    Write-Host "[OK] All services stopped" -ForegroundColor Green
}

function Restart-All {
    Write-Host "`n=== Restarting All Services ===" -ForegroundColor Cyan
    Stop-All
    Start-Sleep -Seconds 2
    Start-Backend
    Start-Frontend
}

function Show-Status {
    Write-Host "`n=== Service Status ===" -ForegroundColor Cyan
    
    $backendRunning = Check-Port -Port 8007
    $frontendRunning = Check-Port -Port 5173
    
    $backendStatus = if ($backendRunning) { "[RUNNING]" } else { "[STOPPED]" }
    $frontendStatus = if ($frontendRunning) { "[RUNNING]" } else { "[STOPPED]" }
    
    $backendColor = if ($backendRunning) { "Green" } else { "Red" }
    $frontendColor = if ($frontendRunning) { "Green" } else { "Red" }
    
    Write-Host "Backend (8007): $backendStatus" -ForegroundColor $backendColor
    Write-Host "Frontend (5173): $frontendStatus" -ForegroundColor $frontendColor
    
    return @{
        Backend = $backendRunning
        Frontend = $frontendRunning
    }
}

function Main {
    param([string]$Command)
    
    if ([string]::IsNullOrEmpty($Command)) {
        Write-Host "`nUsage: .\manage_services.ps1 [command]" -ForegroundColor Cyan
        Write-Host "`nAvailable commands:" -ForegroundColor Yellow
        Write-Host "  start    - Start all services" -ForegroundColor White
        Write-Host "  stop     - Stop all services" -ForegroundColor White
        Write-Host "  restart  - Restart all services" -ForegroundColor White
        Write-Host "  status   - Check service status" -ForegroundColor White
        Write-Host "  backend  - Start backend only" -ForegroundColor White
        Write-Host "  frontend - Start frontend only" -ForegroundColor White
        return
    }
    
    $Command = $Command.ToLower()
    
    switch ($Command) {
        "start" {
            Start-Backend
            Start-Frontend
        }
        "stop" {
            Stop-All
        }
        "restart" {
            Restart-All
        }
        "status" {
            Show-Status
        }
        "backend" {
            Start-Backend
        }
        "frontend" {
            Start-Frontend
        }
        default {
            Write-Host "Unknown command: $Command" -ForegroundColor Red
            Write-Host "Run '.\manage_services.ps1' to see available commands" -ForegroundColor Yellow
        }
    }
}

Main -Command $args[0]
