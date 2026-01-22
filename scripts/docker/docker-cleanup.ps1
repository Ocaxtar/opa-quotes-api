# scripts/docker/docker-cleanup.ps1
# Remove stale/obsolete OPA containers and volumes
#
# Usage: .\scripts\docker\docker-cleanup.ps1 [-Force] [-All]
#
# Options:
#   -Force   Skip confirmation prompt
#   -All     Remove ALL OPA containers (running and stopped)
#
# By default, only removes stopped containers

[CmdletBinding()]
param(
    [switch]$Force,
    [switch]$All
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

function Confirm-Action {
    param([string]$Prompt)
    
    if ($Force) { return $true }
    
    $response = Read-Host "$Prompt (y/N)"
    return $response -eq 'y' -or $response -eq 'Y'
}

function Remove-StoppedContainers {
    Write-Host "=== Containers to Remove ===" -ForegroundColor Cyan
    
    if ($All) {
        $containers = docker ps -a --filter "name=opa-" --format "{{.Names}}" | Sort-Object
    } else {
        $containers = docker ps -a --filter "name=opa-" --filter "status=exited" --filter "status=created" --format "{{.Names}}" | Sort-Object
    }
    
    if (-not $containers) {
        Write-Host "No containers to remove" -ForegroundColor Cyan
        return
    }
    
    $containers | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
    
    $count = ($containers | Measure-Object).Count
    $prompt = "Remove $count container(s)?"
    
    if ($All) {
        $prompt = "⚠️  WARNING: This will remove RUNNING containers! Continue?"
    }
    
    if (Confirm-Action $prompt) {
        Write-Host "Removing containers..." -ForegroundColor Cyan
        $containers | ForEach-Object { docker rm -f $_ 2>$null }
        Write-Host "✓ Containers removed" -ForegroundColor Green
    } else {
        Write-Host "Cancelled" -ForegroundColor Yellow
    }
}

function Remove-DanglingVolumes {
    Write-Host "=== Dangling Volumes to Remove ===" -ForegroundColor Cyan
    
    $volumes = docker volume ls -qf dangling=true | Where-Object { $_ -match 'opa' }
    
    if (-not $volumes) {
        Write-Host "No dangling volumes to remove" -ForegroundColor Cyan
        return
    }
    
    $volumes | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
    
    $count = ($volumes | Measure-Object).Count
    
    if (Confirm-Action "Remove $count dangling volume(s)?") {
        Write-Host "Removing volumes..." -ForegroundColor Cyan
        $volumes | ForEach-Object { docker volume rm $_ 2>$null }
        Write-Host "✓ Volumes removed" -ForegroundColor Green
    } else {
        Write-Host "Cancelled" -ForegroundColor Yellow
    }
}

function Remove-UnusedNetworks {
    Write-Host "=== Unused Networks to Remove ===" -ForegroundColor Cyan
    
    $networks = docker network ls --filter "name=opa-" --format "{{.Name}}" | Where-Object { $_ -notmatch 'bridge|host|none' }
    
    if (-not $networks) {
        Write-Host "No unused networks to remove" -ForegroundColor Cyan
        return
    }
    
    # Filter out networks that are still in use
    $unusedNetworks = @()
    foreach ($net in $networks) {
        $containersUsing = docker network inspect $net --format='{{len .Containers}}' 2>$null
        if ($containersUsing -eq "0") {
            $unusedNetworks += $net
        }
    }
    
    if ($unusedNetworks.Count -eq 0) {
        Write-Host "No unused networks to remove" -ForegroundColor Cyan
        return
    }
    
    $unusedNetworks | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
    
    if (Confirm-Action "Remove $($unusedNetworks.Count) unused network(s)?") {
        Write-Host "Removing networks..." -ForegroundColor Cyan
        $unusedNetworks | ForEach-Object { docker network rm $_ 2>$null }
        Write-Host "✓ Networks removed" -ForegroundColor Green
    } else {
        Write-Host "Cancelled" -ForegroundColor Yellow
    }
}

function Show-DiskSpace {
    Write-Host "`n=== Docker Disk Usage ===" -ForegroundColor Cyan
    docker system df
}

# Main execution
Test-DockerRunning

Write-Host "=== OPA Machine Cleanup ===`n" -ForegroundColor Cyan

if ($All) {
    Write-Host "⚠️  WARNING: -All flag will remove RUNNING containers`n" -ForegroundColor Red
}

# Show current state
Write-Host "Current state:" -ForegroundColor Cyan
docker ps -a --filter "name=opa-" --format "table {{.Names}}`t{{.Status}}"
Write-Host ""

# Execute cleanup steps
Remove-StoppedContainers
Write-Host ""

Remove-DanglingVolumes
Write-Host ""

Remove-UnusedNetworks
Write-Host ""

Show-DiskSpace

Write-Host "`n✓ Cleanup complete" -ForegroundColor Green
Write-Host "`nTo perform a full reset (including volumes), run:"
Write-Host "  .\scripts\docker\docker-reset.ps1"
