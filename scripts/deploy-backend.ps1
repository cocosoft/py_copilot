#!/usr/bin/env pwsh
# ============================================================================
# PyCopilot Backend Deployment Script
# ============================================================================
# Purpose: Deploy the FastAPI backend application
# Requirements: Docker, PowerShell 7+
# ============================================================================

param(
    [string]$Environment = "production",
    [string]$Version = "1.0.0",
    [switch]$Build,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Logs,
    [switch]$Status,
    [switch]$HealthCheck,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Configuration
$BackendDir = Join-Path $ProjectRoot "backend"
$ImageName = "py-copilot-backend"
$ContainerName = "py-copilot-backend-prod"
$Port = 8000
$HealthCheckInterval = 30

# Colors for output
$Colors = @{
    Info = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO]" -ForegroundColor $Colors.Info -NoNewline
    Write-Host " $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS]" -ForegroundColor $Colors.Success -NoNewline
    Write-Host " $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING]" -ForegroundColor $Colors.Warning -NoNewline
    Write-Host " $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR]" -ForegroundColor $Colors.Error -NoNewline
    Write-Host " $Message"
}

function Show-Help {
    Write-Host @"
PyCopilot Backend Deployment Script

Usage: .\deploy-backend.ps1 [Options]

Options:
    -Environment <env>    Deployment environment (development|staging|production)
                          Default: production
    -Version <version>    Application version tag
                          Default: 1.0.0
    -Build                Build the Docker image
    -Start                Start the container
    -Stop                 Stop the container
    -Restart              Restart the container
    -Logs                 Show container logs
    -Status               Show container status
    -HealthCheck          Perform health check
    -Help                 Show this help message

Examples:
    .\deploy-backend.ps1 -Build -Start -Environment production
    .\deploy-backend.ps1 -Restart -Version 1.0.1
    .\deploy-backend.ps1 -Logs -Status
    .\deploy-backend.ps1 -HealthCheck

Environment Variables:
    DATABASE_URL      Database connection string
    REDIS_URL         Redis connection string
    SECRET_KEY        Application secret key
    LOG_LEVEL         Logging level (DEBUG|INFO|WARNING|ERROR)
    METRICS_ENABLED   Enable Prometheus metrics (true|false)

"@
}

function Get-EnvironmentConfig {
    param([string]$Env)
    
    $config = @{
        Environment = $Env
        Debug = $false
        LogLevel = "INFO"
        MetricsEnabled = $true
        Workers = 4
        Port = $Port
    }
    
    switch ($Env) {
        "development" {
            $config.Debug = $true
            $config.LogLevel = "DEBUG"
            $config.Workers = 1
        }
        "staging" {
            $config.Debug = $false
            $config.LogLevel = "DEBUG"
            $config.Workers = 2
        }
        "production" {
            $config.Debug = $false
            $config.LogLevel = "INFO"
            $config.Workers = 4
        }
    }
    
    return $config
}

function Test-Docker {
    Write-Info "Checking Docker installation..."
    try {
        $dockerVersion = docker --version
        if ($LASTEXITCODE -ne 0) {
            throw "Docker is not installed or not in PATH"
        }
        Write-Success "Docker found: $dockerVersion"
        return $true
    }
    catch {
        Write-Error "Docker check failed: $_"
        return $false
    }
}

function Test-Dockerfile {
    param([string]$Dir)
    
    Write-Info "Checking for Dockerfile in $Dir..."
    $dockerfilePath = Join-Path $Dir "Dockerfile"
    
    if (-not (Test-Path $dockerfilePath)) {
        Write-Error "Dockerfile not found at $dockerfilePath"
        return $false
    }
    
    Write-Success "Dockerfile found"
    return $true
}

function Get-ContainerStatus {
    param([string]$Name)
    
    $status = docker ps -a --filter "name=$Name" --format "{{.Names}}:{{.Status}}"
    if ($status) {
        return @{
            Running = $status -match "Up"
            Status = $status
        }
    }
    return @{
        Running = $false
        Status = "Not found"
    }
}

function Build-Image {
    param([string]$Version)
    
    Write-Info "Building backend Docker image..."
    $fullImageName = "${ImageName}:$Version"
    
    try {
        $envConfig = Get-EnvironmentConfig -Env $Environment
        
        # Build with build args
        $buildArgs = @(
            "--build-arg", "ENVIRONMENT=$Environment",
            "--build-arg", "PYTHON_VERSION=3.11-slim",
            "-t", $fullImageName,
            "-f", "Dockerfile",
            "."
        )
        
        # Add version tag
        $latestTag = "${ImageName}:latest"
        $buildArgs += "-t", $latestTag
        
        docker build @buildArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Image built successfully: $fullImageName"
            Write-Success "Also tagged as: $latestTag"
            return $true
        }
        else {
            Write-Error "Image build failed"
            return $false
        }
    }
    catch {
        Write-Error "Build error: $_"
        return $false
    }
}

function Start-Container {
    param([string]$Version)
    
    Write-Info "Starting backend container..."
    $containerInfo = Get-ContainerStatus -Name $ContainerName
    
    # Stop existing container if running
    if ($containerInfo.Running) {
        Write-Warning "Container $ContainerName is already running"
        $response = Read-Host "Do you want to restart it? (y/n)"
        if ($response.ToLower() -ne "y") {
            Write-Info "Aborting start"
            return $true
        }
        Stop-Container
    }
    
    $envConfig = Get-EnvironmentConfig -Env $Environment
    $imageName = "${ImageName}:$Version"
    
    # Check if image exists
    $imageExists = docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -eq $imageName }
    if (-not $imageExists) {
        Write-Warning "Image $imageName not found. Building..."
        if (-not (Build-Image -Version $Version)) {
            return $false
        }
    }
    
    # Build docker run command
    $runArgs = @(
        "run", "-d",
        "--name", $ContainerName,
        "--restart", "unless-stopped",
        "-p", "$($envConfig.Port):8000",
        "-e", "ENVIRONMENT=$Environment",
        "-e", "DEBUG=$($envConfig.Debug)",
        "-e", "LOG_LEVEL=$($envConfig.LogLevel)",
        "-e", "METRICS_ENABLED=$($envConfig.MetricsEnabled)",
        "-e", "WORKERS=$($envConfig.Workers)",
        "-e", "API_V1_STR=/api/v1",
        "-e", "PROJECT_NAME=PyCopilot Backend"
    )
    
    # Add environment variables if set
    if ($env:DATABASE_URL) {
        $runArgs += "-e", "DATABASE_URL=$env:DATABASE_URL"
    }
    if ($env:REDIS_URL) {
        $runArgs += "-e", "REDIS_URL=$env:REDIS_URL"
    }
    if ($env:SECRET_KEY) {
        $runArgs += "-e", "SECRET_KEY=$env:SECRET_KEY"
    }
    if ($env:OPENAI_API_KEY) {
        $runArgs += "-e", "OPENAI_API_KEY=$env:OPENAI_API_KEY"
    }
    if ($env:HUGGINGFACE_API_TOKEN) {
        $runArgs += "-e", "HUGGINGFACE_API_TOKEN=$env:HUGGINGFACE_API_TOKEN"
    }
    
    # Mount volumes for data persistence
    $runArgs += "-v", (Join-Path $BackendDir "data:/app/data")
    $runArgs += "-v", (Join-Path $BackendDir "logs:/app/logs")
    
    # Add health check
    $runArgs += "--health-cmd", "curl -f http://localhost:8000/health || exit 1"
    $runArgs += "--health-interval", "${HealthCheckInterval}s"
    $runArgs += "--health-timeout", "10s"
    $runArgs += "--health-retries", "3"
    
    # Add the image name
    $runArgs += $imageName
    
    try {
        docker @runArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Container started: $ContainerName"
            Start-Sleep -Seconds 3
            
            # Wait for container to be healthy
            Wait-ForContainerHealth -Name $ContainerName -Timeout 60
            return $true
        }
        else {
            Write-Error "Failed to start container"
            return $false
        }
    }
    catch {
        Write-Error "Start error: $_"
        return $false
    }
}

function Stop-Container {
    param([switch]$Force)
    
    Write-Info "Stopping container $ContainerName..."
    $containerInfo = Get-ContainerStatus -Name $ContainerName
    
    if (-not $containerInfo.Running) {
        Write-Warning "Container $ContainerName is not running"
        return $true
    }
    
    $stopArgs = @("stop")
    if ($Force) {
        $stopArgs += "-t", "0"
    }
    $stopArgs += $ContainerName
    
    try {
        docker @stopArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Container stopped: $ContainerName"
            return $true
        }
        else {
            Write-Error "Failed to stop container"
            return $false
        }
    }
    catch {
        Write-Error "Stop error: $_"
        return $false
    }
}

function Remove-Container {
    Write-Info "Removing container $ContainerName..."
    
    $containerInfo = Get-ContainerStatus -Name $ContainerName
    if ($containerInfo.Running) {
        Stop-Container
    }
    
    try {
        docker rm $ContainerName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Container removed: $ContainerName"
            return $true
        }
        else {
            Write-Error "Failed to remove container"
            return $false
        }
    }
    catch {
        Write-Error "Remove error: $_"
        return $false
    }
}

function Show-Logs {
    param([switch]$Follow, [int]$Lines = 50)
    
    Write-Info "Showing logs for $ContainerName..."
    
    $logArgs = @("logs")
    if ($Follow) {
        $logArgs += "-f"
    }
    $logArgs += "--tail", $Lines
    $logArgs += $ContainerName
    
    docker @logArgs
}

function Show-Status {
    Write-Info "Container Status:"
    $containerInfo = Get-ContainerStatus -Name $ContainerName
    
    Write-Host "  Name: $ContainerName"
    Write-Host "  Status: $($containerInfo.Status)"
    
    if ($containerInfo.Running) {
        # Get container details
        $inspect = docker inspect $ContainerName --format "{{json .Config}}" | ConvertFrom-Json
        Write-Host "  Image: $($inspect.Image)"
        Write-Host "  Ports: $($inspect.HostConfig.PortBindings | ConvertTo-Json -Compress)"
    }
}

function Perform-HealthCheck {
    Write-Info "Performing health check..."
    $containerInfo = Get-ContainerStatus -Name $ContainerName
    
    if (-not $containerInfo.Running) {
        Write-Error "Container is not running"
        return $false
    }
    
    # Check Docker health status
    $healthStatus = docker inspect $ContainerName --format "{{.State.Health.Status}}"
    Write-Host "  Docker Health: $healthStatus"
    
    # Check API endpoint
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$Port/health" -TimeoutSec 10
        Write-Host "  API Health: OK"
        Write-Host "  Version: $($response.version)"
        Write-Host "  Environment: $($response.environment)"
        return $true
    }
    catch {
        Write-Warning "API health check failed: $_"
        return $false
    }
}

function Wait-ForContainerHealth {
    param(
        [string]$Name,
        [int]$Timeout = 60
    )
    
    Write-Info "Waiting for container to be healthy..."
    $startTime = Get-Date
    
    while ((Get-Date) - $startTime -lt (New-TimeSpan -Seconds $Timeout)) {
        $healthStatus = docker inspect $Name --format "{{.State.Health.Status}}" 2>$null
        if ($healthStatus -eq "healthy") {
            Write-Success "Container is healthy"
            return $true
        }
        Start-Sleep -Seconds 5
    }
    
    Write-Warning "Timeout waiting for container health"
    return $false
}

function Restart-Container {
    Write-Info "Restarting container..."
    Stop-Container
    Start-Sleep -Seconds 5
    Start-Container -Version $Version
}

# Main execution
function Main {
    if ($Help) {
        Show-Help
        exit 0
    }
    
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  PyCopilot Backend Deployment Script" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "Environment: $Environment"
    Write-Info "Version: $Version"
    Write-Host ""
    
    # Check prerequisites
    if (-not (Test-Docker)) {
        exit 1
    }
    
    if (-not (Test-Dockerfile -Dir $ProjectRoot)) {
        exit 1
    }
    
    # Execute requested actions
    $actionsCompleted = 0
    
    if ($Build) {
        $actionsCompleted++
        if (Build-Image -Version $Version) {
            Write-Success "Build action completed"
        } else {
            exit 1
        }
    }
    
    if ($Stop) {
        $actionsCompleted++
        if (Stop-Container) {
            Write-Success "Stop action completed"
        } else {
            exit 1
        }
    }
    
    if ($Start) {
        $actionsCompleted++
        if (Start-Container -Version $Version) {
            Write-Success "Start action completed"
        } else {
            exit 1
        }
    }
    
    if ($Restart) {
        $actionsCompleted++
        Restart-Container
        Write-Success "Restart action completed"
    }
    
    if ($Status) {
        $actionsCompleted++
        Show-Status
    }
    
    if ($Logs) {
        $actionsCompleted++
        Show-Logs -Lines 100
    }
    
    if ($HealthCheck) {
        $actionsCompleted++
        if (Perform-HealthCheck) {
            Write-Success "Health check passed"
        } else {
            Write-Warning "Health check failed"
        }
    }
    
    # Default action if no specific action requested
    if ($actionsCompleted -eq 0) {
        Write-Info "No action specified. Showing status..."
        Show-Status
        Write-Host ""
        Write-Info "Use -Help to see available options"
    }
    
    Write-Host ""
    Write-Info "Deployment script completed"
}

# Run main function
Main
