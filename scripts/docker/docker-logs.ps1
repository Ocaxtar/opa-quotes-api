# scripts/docker/docker-logs.ps1
# Tail logs of OPA services
#
# Usage: .\scripts\docker\docker-logs.ps1 [container_name] [-Follow] [-Lines NUM] [-Timestamps] [-Since DURATION]
#
# Options:
#   -Follow      Follow log output (like tail -f)
#   -Lines NUM   Number of lines to show (default: 50)
#   -Timestamps  Show timestamps
#   -Since       Show logs since duration (e.g., 10m, 1h)
#
# If no container specified, shows interactive menu

[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string]$Container,
    
    [switch]$Follow,
    
    [int]$Lines = 50,
    
    [switch]$Timestamps,
    
    [string]$Since
)

$ErrorActionPreference = "Stop"

function Test-DockerRunning {
    try {
        docker info 2>$null | Out-Null
        return $true
    } catch {
        Write-Host "Error: Docker is not running" -ForegroundColor Red
        exit 1
    }
}

function Get-OpaContainers {
    return docker ps -a --filter "name=opa-" --format "{{.Names}}" | Sort-Object
}

function Show-Menu {
    $containers = Get-OpaContainers
    
    if (-not $containers) {
        Write-Host "No OPA containers found" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "=== Select Container ===`n" -ForegroundColor Cyan
    
    $containerArray = @()
    $index = 1
    
    foreach ($cont in $containers) {
        $status = docker inspect --format='{{.State.Status}}' $cont
        $indicator = switch ($status) {
            "running" { Write-Host "●" -ForegroundColor Green -NoNewline; " " }
            "exited" { Write-Host "●" -ForegroundColor Red -NoNewline; " " }
            default { Write-Host "●" -ForegroundColor Yellow -NoNewline; " " }
        }
        
        Write-Host "  $index) $cont"
        $containerArray += $cont
        $index++
    }
    
    Write-Host ""
    $selection = Read-Host "Select container (1-$($containerArray.Count))"
    
    if ($selection -match '^\d+$' -and [int]$selection -ge 1 -and [int]$selection -le $containerArray.Count) {
        return $containerArray[[int]$selection - 1]
    } else {
        Write-Host "Invalid selection" -ForegroundColor Red
        exit 1
    }
}

function Build-LogsCommand {
    param([string]$TargetContainer)
    
    $cmd = @("docker", "logs")
    
    if ($Follow) {
        $cmd += "--follow"
    }
    
    if ($Timestamps) {
        $cmd += "--timestamps"
    }
    
    if ($Since) {
        $cmd += "--since", $Since
    } else {
        $cmd += "--tail", $Lines
    }
    
    $cmd += $TargetContainer
    
    return $cmd
}

function Show-Logs {
    param([string]$TargetContainer)
    
    # Check if container exists
    try {
        docker inspect $TargetContainer 2>$null | Out-Null
    } catch {
        Write-Host "Container '$TargetContainer' not found" -ForegroundColor Red
        
        Write-Host "`nAvailable OPA containers:" -ForegroundColor Yellow
        Get-OpaContainers | ForEach-Object { Write-Host "  $_" }
        exit 1
    }
    
    # Build and show header
    Write-Host "=== Logs for $TargetContainer ===" -ForegroundColor Cyan
    
    $status = docker inspect --format='{{.State.Status}}' $TargetContainer
    Write-Host "Status: $status" -ForegroundColor Yellow
    
    if ($Follow) {
        Write-Host "Following logs (Ctrl+C to stop)..." -ForegroundColor Yellow
    } else {
        Write-Host "Showing last $Lines lines..." -ForegroundColor Yellow
    }
    
    Write-Host ("-" * 80)
    Write-Host ""
    
    # Execute logs command
    $cmd = Build-LogsCommand $TargetContainer
    
    if ($Follow) {
        # For follow mode, use native streaming
        & $cmd[0] $cmd[1..($cmd.Length-1)]
    } else {
        # For non-follow mode, capture and display
        $logs = & $cmd[0] $cmd[1..($cmd.Length-1)] 2>&1
        
        if ($logs) {
            $logs | ForEach-Object { Write-Host $_ }
        } else {
            Write-Host "(no logs)" -ForegroundColor Yellow
        }
    }
}

function Show-AllLogs {
    $containers = Get-OpaContainers
    
    if (-not $containers) {
        Write-Host "No OPA containers found" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "=== Logs from all OPA containers ===" -ForegroundColor Cyan
    Write-Host "Showing last $Lines lines per container...`n" -ForegroundColor Yellow
    
    foreach ($cont in $containers) {
        Write-Host ("-" * 80)
        Write-Host "Container: $cont" -ForegroundColor Cyan
        Write-Host ("-" * 80)
        
        $logs = docker logs --tail $Lines $cont 2>&1
        if ($logs) {
            $logs | ForEach-Object { Write-Host $_ }
        } else {
            Write-Host "(no logs)" -ForegroundColor Yellow
        }
        
        Write-Host ""
    }
}

# Main execution
Test-DockerRunning

if ($Container -eq "all") {
    # Show logs from all containers
    Show-AllLogs
} elseif ($Container) {
    # Show logs for specified container
    Show-Logs $Container
} else {
    # Interactive menu
    $selectedContainer = Show-Menu
    Show-Logs $selectedContainer
}
