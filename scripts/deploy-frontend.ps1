#!/usr/bin/env pwsh
# ============================================================================
# PyCopilot Frontend & Desktop Deployment Script
# ============================================================================
# Purpose: Deploy the React frontend and Electron desktop application
# Requirements: Docker, Node.js 18+, PowerShell 7+
# ============================================================================

param(
    [string]$Environment = "production",
    [string]$Version = "1.0.0",
    [ValidateSet("web", "desktop", "all")]
    [string]$Target = "web",
    [ValidateSet("docker", "npm", "electron-builder")]
    [string]$BuildMethod = "docker",
    [switch]$Build,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Logs,
    [switch]$Status,
    [switch]$HealthCheck,
    [ValidateSet("win", "mac", "linux", "all")]
    [string]$Platform = "win",
    [switch]$Package,
    [switch]$Install,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Configuration
$FrontendDir = Join-Path $ProjectRoot "frontend"
$ElectronDir = Join-Path $ProjectRoot "electron"
$WebImageName = "py-copilot-frontend"
$WebContainerName = "py-copilot-frontend-prod"
$ElectronContainerName = "py-copilot-electron-prod"
$WebPort = 80
$DesktopPort = 3000
$ReleaseDir = Join-Path $ElectronDir "release"

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
PyCopilot Frontend & Desktop Deployment Script

Usage: .\deploy-frontend.ps1 [Options]

Options:
    -Environment <env>    Deployment environment (development|staging|production)
                          Default: production
    -Version <version>    Application version tag
                          Default: 1.0.0
    -Target <target>      Deployment target (web|desktop|all)
                          Default: web
    -BuildMethod <method> Build method (docker|npm|electron-builder)
                          Default: docker (for web), npm (for desktop)
    -Build                Build the application(s)
    -Start                Start the container/service
    -Stop                 Stop the container/service
    -Restart              Restart the container/service
    -Logs                 Show container/service logs
    -Status               Show container/service status
    -HealthCheck          Perform health check
    -Platform <platform>  Target platform for desktop build (win|mac|linux|all)
                          Default: win
    -Package              Package the desktop application
    -Install              Install desktop application (platform-specific)
    -Help                 Show this help message

Examples:
    # Build and deploy web frontend using Docker
    .\deploy-frontend.ps1 -Build -Start -Environment production
    
    # Build desktop installer for Windows
    .\deploy-frontend.ps1 -Target desktop -Build -Package -Platform win
    
    # Build all platforms
    .\deploy-frontend.ps1 -Target desktop -Build -Package -Platform all
    
    # View logs
    .\deploy-frontend.ps1 -Logs
    
    # Check status and health
    .\deploy-frontend.ps1 -Status -HealthCheck

Deployment Modes:
    web (Docker):     Containerized Nginx serving built React app
    web (npm):        Development server using Vite
    desktop:          Electron application packaging

Environment Variables:
    VITE_API_URL          Backend API URL
    VITE_WS_URL           WebSocket URL
    ELECTRON_NPM_MIRROR   NPM mirror for Electron builds

"@
}

function Get-EnvironmentConfig {
    param([string]$Env)
    
    $config = @{
        Environment = $Env
        Debug = $false
        API_URL = "http://localhost:8000"
        WS_URL = "ws://localhost:8000"
        Port = $WebPort
    }
    
    switch ($Env) {
        "development" {
            $config.Debug = $true
            $config.API_URL = "http://localhost:8000"
            $config.WS_URL = "ws://localhost:8000"
            $config.Port = $DesktopPort
        }
        "staging" {
            $config.Debug = $false
            $config.API_URL = "http://staging-api.example.com"
            $config.WS_URL = "ws://staging-api.example.com"
        }
        "production" {
            $config.Debug = $false
            $config.API_URL = "http://api.example.com"
            $config.WS_URL = "ws://api.example.com"
        }
    }
    
    return $config
}

function Test-NodeVersion {
    Write-Info "Checking Node.js installation..."
    try {
        $nodeVersion = node --version
        $npmVersion = npm --version
        Write-Success "Node.js found: $nodeVersion"
        Write-Success "NPM found: $npmVersion"
        
        # Check if version is 18+
        $versionNumber = [version]$nodeVersion.Replace('v', '')
        if ($versionNumber.Major -lt 18) {
            Write-Warning "Node.js 18+ is recommended"
        }
        return $true
    }
    catch {
        Write-Error "Node.js check failed: $_"
        return $false
    }
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

function Test-ElectronBuilder {
    Write-Info "Checking Electron Builder..."
    try {
        $builderVersion = npx electron-builder --version
        Write-Success "Electron Builder found: $builderVersion"
        return $true
    }
    catch {
        Write-Warning "Electron Builder not found. Installing..."
        return $false
    }
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

function Build-WebDocker {
    param([string]$Version)
    
    Write-Info "Building web frontend Docker image..."
    $fullImageName = "${WebImageName}:$Version"
    
    try {
        # Multi-stage build
        $buildArgs = @(
            "-f", "Dockerfile",
            "-t", $fullImageName,
            "-t", "${WebImageName}:latest",
            "."
        )
        
        docker build @buildArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Web image built successfully: $fullImageName"
            return $true
        }
        else {
            Write-Error "Web image build failed"
            return $false
        }
    }
    catch {
        Write-Error "Web build error: $_"
        return $false
    }
}

function Build-WebNPM {
    param([string]$Env)
    
    Write-Info "Building web frontend with NPM..."
    
    try {
        $envConfig = Get-EnvironmentConfig -Env $Env
        
        # Set environment variables
        $env:VITE_API_URL = $envConfig.API_URL
        $env:VITE_WS_URL = $envConfig.WS_URL
        $env:NODE_ENV = $Env
        
        # Install dependencies
        Write-Info "Installing dependencies..."
        Push-Location $FrontendDir
        npm ci --prefer-offline --no-audit
        
        if ($LASTEXITCODE -ne 0) {
            throw "npm ci failed"
        }
        
        # Build
        Write-Info "Building application..."
        npm run build
        
        if ($LASTEXITCODE -ne 0) {
            throw "npm build failed"
        }
        
        Pop-Location
        Write-Success "Web build completed successfully"
        return $true
    }
    catch {
        Write-Error "Web build error: $_"
        Pop-Location
        return $false
    }
}

function Build-Desktop {
    param([string]$Platform, [string]$Version)
    
    Write-Info "Building Electron desktop application..."
    Write-Info "Target platform: $Platform"
    
    try {
        Push-Location $ElectronDir
        
        # Build React frontend first
        Write-Info "Building React frontend for Electron..."
        Push-Location $FrontendDir
        $env:VITE_API_URL = "http://localhost:8000"
        $env:VITE_WS_URL = "ws://localhost:8000"
        npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "React build failed"
        }
        Pop-Location
        
        # Build Electron
        Write-Info "Building Electron application..."
        
        $buildArgs = @("run", "build:electron")
        
        # Add platform-specific arguments
        switch ($Platform) {
            "win" {
                $buildArgs += "--win"
            }
            "mac" {
                $buildArgs += "--mac"
            }
            "linux" {
                $buildArgs += "--linux"
            }
            "all" {
                $buildArgs += "--win", "--mac", "--linux"
            }
        }
        
        npm @buildArgs
        
        if ($LASTEXITCODE -ne 0) {
            throw "Electron build failed"
        }
        
        Pop-Location
        Write-Success "Desktop build completed successfully"
        Write-Info "Output available in: $ReleaseDir"
        return $true
    }
    catch {
        Write-Error "Desktop build error: $_"
        Pop-Location
        return $false
    }
}

function Start-WebContainer {
    param([string]$Version)
    
    Write-Info "Starting web frontend container..."
    $containerInfo = Get-ContainerStatus -Name $WebContainerName
    
    if ($containerInfo.Running) {
        Write-Warning "Container $WebContainerName is already running"
        return $true
    }
    
    $imageName = "${WebImageName}:$Version"
    
    # Check if image exists
    $imageExists = docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -eq $imageName }
    if (-not $imageExists) {
        Write-Warning "Image $imageName not found. Building..."
        if (-not (Build-WebDocker -Version $Version)) {
            return $false
        }
    }
    
    try {
        $runArgs = @(
            "run", "-d",
            "--name", $WebContainerName,
            "--restart", "unless-stopped",
            "-p", "$WebPort:80",
            "-e", "ENVIRONMENT=$Environment",
            "-v", (Join-Path $FrontendDir "nginx-cache:/var/cache/nginx"),
            "-v", (Join-Path $FrontendDir "nginx-logs:/var/log/nginx"),
            "--health-cmd", "wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1",
            "--health-interval", "30s",
            "--health-timeout", "10s",
            "--health-retries", "3",
            $imageName
        )
        
        docker @runArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Web container started: $WebContainerName"
            Start-Sleep -Seconds 3
            return $true
        }
        else {
            Write-Error "Failed to start web container"
            return $false
        }
    }
    catch {
        Write-Error "Start error: $_"
        return $false
    }
}

function Start-WebDevServer {
    param([string]$Env)
    
    Write-Info "Starting web development server..."
    
    try {
        $envConfig = Get-EnvironmentConfig -Env $Env
        $env:VITE_API_URL = $envConfig.API_URL
        $env:VITE_WS_URL = $envConfig.WS_URL
        $env:NODE_ENV = $Env
        
        Push-Location $FrontendDir
        
        # Start in background
        $process = Start-Process -FilePath "npm" -ArgumentList @("run", "dev", "--host", "--port", $envConfig.Port) -PassThru -NoNewWindow
        
        Pop-Location
        
        Write-Success "Development server started on port $($envConfig.Port)"
        return $true
    }
    catch {
        Write-Error "Start error: $_"
        return $false
    }
}

function Start-DesktopDevServer {
    Write-Info "Starting Electron development server..."
    
    try {
        Push-Location $ElectronDir
        $process = Start-Process -FilePath "npm" -ArgumentList @("run", "dev") -PassThru -NoNewWindow
        Pop-Location
        
        Write-Success "Electron development server started"
        return $true
    }
    catch {
        Write-Error "Start error: $_"
        return $false
    }
}

function Stop-Container {
    param([string]$Name)
    
    Write-Info "Stopping container $Name..."
    $containerInfo = Get-ContainerStatus -Name $Name
    
    if (-not $containerInfo.Running) {
        Write-Warning "Container $Name is not running"
        return $true
    }
    
    try {
        docker stop $Name | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Container stopped: $Name"
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

function Show-WebLogs {
    param([switch]$Follow, [int]$Lines = 50)
    
    Write-Info "Showing logs for $WebContainerName..."
    $logArgs = @("logs")
    if ($Follow) {
        $logArgs += "-f"
    }
    $logArgs += "--tail", $Lines, $WebContainerName
    
    docker @logArgs
}

function Show-Status {
    Write-Info "Container Status:"
    
    # Web container
    $webInfo = Get-ContainerStatus -Name $WebContainerName
    Write-Host "  Web Container: $WebContainerName"
    Write-Host "    Status: $($webInfo.Status)"
    
    if ($webInfo.Running) {
        $inspect = docker inspect $WebContainerName --format "{{json .Config}}" 2>$null | ConvertFrom-Json
        Write-Host "    Image: $($inspect.Image)"
    }
    
    Write-Host ""
    
    # Desktop container (if exists)
    $desktopInfo = Get-ContainerStatus -Name $ElectronContainerName
    Write-Host "  Desktop Container: $ElectronContainerName"
    Write-Host "    Status: $($desktopInfo.Status)"
}

function Perform-HealthCheck {
    Write-Info "Performing health check..."
    
    # Check web container
    $webInfo = Get-ContainerStatus -Name $WebContainerName
    if ($webInfo.Running) {
        $healthStatus = docker inspect $WebContainerName --format "{{.State.Health.Status}}" 2>$null
        Write-Host "  Web Docker Health: $healthStatus"
        
        # Check HTTP endpoint
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$WebPort/" -TimeoutSec 10 -UseBasicParsing
            Write-Host "  Web HTTP Status: $($response.StatusCode)"
        }
        catch {
            Write-Warning "Web HTTP check failed: $_"
        }
    }
    else {
        Write-Warning "Web container is not running"
    }
    
    return $true
}

function Install-DesktopApp {
    param([string]$Platform)
    
    Write-Info "Installing desktop application..."
    
    try {
        Push-Location $ReleaseDir
        
        switch ($Platform) {
            "win" {
                $installer = Get-ChildItem -Filter "*.exe" | Select-Object -First 1
                if ($installer) {
                    Write-Info "Running installer: $($installer.FullName)"
                    Start-Process -FilePath $installer.FullName -Wait
                    Write-Success "Desktop application installed"
                }
                else {
                    Write-Error "No Windows installer found"
                }
            }
            "mac" {
                $dmg = Get-ChildItem -Filter "*.dmg" | Select-Object -First 1
                if ($dmg) {
                    Write-Info "DMG file: $($dmg.FullName)"
                    Write-Info "Please mount and install the DMG manually"
                }
                else {
                    Write-Error "No macOS DMG found"
                }
            }
            "linux" {
                $deb = Get-ChildItem -Filter "*.deb" | Select-Object -First 1
                if ($deb) {
                    Write-Info "Installing DEB package: $($deb.FullName)"
                    Start-Process -FilePath "dpkg" -ArgumentList @("-i", $deb.FullName) -Wait -PassThru
                    Write-Success "Desktop application installed"
                }
                else {
                    Write-Error "No Linux DEB found"
                }
            }
        }
        
        Pop-Location
        return $true
    }
    catch {
        Write-Error "Install error: $_"
        Pop-Location
        return $false
    }
}

# Main execution
function Main {
    if ($Help) {
        Show-Help
        exit 0
    }
    
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  PyCopilot Frontend & Desktop Deployment" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "Environment: $Environment"
    Write-Info "Version: $Version"
    Write-Info "Target: $Target"
    Write-Host ""
    
    # Check prerequisites based on target and build method
    if ($Target -eq "web" -and $BuildMethod -eq "docker") {
        if (-not (Test-Docker)) {
            exit 1
        }
    }
    
    if ($Target -eq "desktop" -or ($Target -eq "web" -and $BuildMethod -eq "npm")) {
        if (-not (Test-NodeVersion)) {
            exit 1
        }
    }
    
    # Execute requested actions
    if ($Build) {
        switch ($Target) {
            "web" {
                if ($BuildMethod -eq "docker") {
                    if (-not (Build-WebDocker -Version $Version)) {
                        exit 1
                    }
                }
                else {
                    if (-not (Build-WebNPM -Env $Environment)) {
                        exit 1
                    }
                }
            }
            "desktop" {
                if (-not (Build-Desktop -Platform $Platform -Version $Version)) {
                    exit 1
                }
            }
            "all" {
                if (-not (Build-WebDocker -Version $Version)) {
                    exit 1
                }
                if (-not (Build-Desktop -Platform $Platform -Version $Version)) {
                    exit 1
                }
            }
        }
        Write-Success "Build action completed"
    }
    
    if ($Package) {
        if ($Target -ne "desktop") {
            Write-Warning "Package only applies to desktop target"
        }
        else {
            if (-not (Build-Desktop -Platform $Platform -Version $Version)) {
                exit 1
            }
            Write-Success "Package action completed"
        }
    }
    
    if ($Install) {
        if (-not (Install-DesktopApp -Platform $Platform)) {
            exit 1
        }
    }
    
    if ($Stop) {
        if ($Target -eq "web" -or $Target -eq "all") {
            Stop-Container -Name $WebContainerName | Out-Null
        }
        if ($Target -eq "desktop" -or $Target -eq "all") {
            Stop-Container -Name $ElectronContainerName | Out-Null
        }
    }
    
    if ($Start) {
        if ($Target -eq "web") {
            if ($BuildMethod -eq "docker") {
                if (-not (Start-WebContainer -Version $Version)) {
                    exit 1
                }
            }
            else {
                if (-not (Start-WebDevServer -Env $Environment)) {
                    exit 1
                }
            }
        }
        elseif ($Target -eq "desktop") {
            if (-not (Start-DesktopDevServer)) {
                exit 1
            }
        }
        else {
            if (-not (Start-WebContainer -Version $Version)) {
                exit 1
            }
        }
        Write-Success "Start action completed"
    }
    
    if ($Status) {
        Show-Status
    }
    
    if ($Logs) {
        Show-WebLogs -Lines 100
    }
    
    if ($HealthCheck) {
        Perform-HealthCheck
    }
    
    # Default action if no specific action requested
    $anyAction = $Build -or $Start -or $Stop -or $Restart -or $Status -or $Logs -or $HealthCheck -or $Package -or $Install
    if (-not $anyAction) {
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
